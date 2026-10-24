package de.spaceage.feinschliff;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.Handler;
import android.os.Looper;
import android.view.HapticFeedbackConstants;
import android.view.MotionEvent;
import android.view.View;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Draws the keys and turns touches into key presses (tap, long-press alternates, repeating delete, swipe). */
final class KeyboardView extends View {
    static final int SHIFT = -1, DELETE = -2, SYMBOLS = -3, LETTERS = -4, MORE = -5, ENTER = -6, SPACE = -7, SWITCH = -8, EMOJI = -9;

    interface Listener {
        void onText(String text);
        void onCode(int code);
        void onSwitchLongPress();
        /** A finger path across the letter keys; shift/caps as they were when it started. */
        void onSwipe(float[] xs, float[] ys, boolean shift, boolean caps);
    }

    static final class Key {
        final String label;
        final int code;          // 0 = types its label
        final float weight;
        final String[] alts;
        final RectF rect = new RectF();

        Key(String label, int code, float weight, String... alts) {
            this.label = label;
            this.code = code;
            this.weight = weight;
            this.alts = alts;
        }
    }

    // --- layouts
    private static final String[][] LETTER_ALTS = {
            {"q", "1"}, {"w", "2"}, {"e", "3", "é", "è", "ê", "€"}, {"r", "4"}, {"t", "5"}, {"z", "6"},
            {"u", "7", "ú", "ù", "û"}, {"i", "8", "í", "ì", "î"}, {"o", "9", "ó", "ò", "ô", "œ"}, {"p", "0"},
            {"a", "à", "á", "â", "æ"}, {"s", "ß", "$", "§"}, {"c", "ç", "©"}, {"n", "ñ"}, {"y", "ý"},
    };

    private static List<Key> row(String chars) {
        List<Key> r = new ArrayList<Key>();
        for (String c : chars.split(" ")) r.add(new Key(c, 0, 1f, alts(c)));
        return r;
    }

    private static String[] alts(String c) {
        for (String[] a : LETTER_ALTS) {
            if (a[0].equals(c)) {
                String[] out = new String[a.length - 1];
                System.arraycopy(a, 1, out, 0, out.length);
                return out;
            }
        }
        return new String[0];
    }

    private static List<List<Key>> letters(String enterLabel) {
        List<List<Key>> rows = new ArrayList<List<Key>>();
        rows.add(row("q w e r t z u i o p ü"));
        rows.add(row("a s d f g h j k l ö ä"));
        List<Key> r3 = new ArrayList<Key>();
        r3.add(new Key("⇧", SHIFT, 1.5f));
        r3.addAll(row("y x c v b n m"));
        r3.add(new Key("⌫", DELETE, 1.5f));
        rows.add(r3);
        rows.add(bottom("?123", SYMBOLS, enterLabel));
        return rows;
    }

    private static List<List<Key>> symbols(String enterLabel, boolean more) {
        List<List<Key>> rows = new ArrayList<List<Key>>();
        if (!more) {
            rows.add(row("1 2 3 4 5 6 7 8 9 0"));
            rows.add(row("@ # € & _ - ( ) / : ;"));
            List<Key> r3 = new ArrayList<Key>();
            r3.add(new Key("=\\<", MORE, 1.5f));
            r3.addAll(row("* \" ' ! ? + %"));
            r3.add(new Key("⌫", DELETE, 1.5f));
            rows.add(r3);
        } else {
            rows.add(row("~ ` | • √ π ÷ × ¶ ∆"));
            rows.add(row("£ ¥ $ ¢ ^ ° = { } \\"));
            List<Key> r3 = new ArrayList<Key>();
            r3.add(new Key("?123", SYMBOLS, 1.5f));
            r3.addAll(row("[ ] < > « » …"));
            r3.add(new Key("⌫", DELETE, 1.5f));
            rows.add(r3);
        }
        rows.add(bottom("ABC", LETTERS, enterLabel));
        return rows;
    }

    private static List<Key> bottom(String modeLabel, int modeCode, String enterLabel) {
        List<Key> r = new ArrayList<Key>();
        r.add(new Key(modeLabel, modeCode, 1.5f));
        r.add(new Key("🌐", SWITCH, 1f));
        r.add(new Key("😊", EMOJI, 1f));
        r.add(new Key(",", 0, 1f));
        r.add(new Key("Leertaste", SPACE, 3.5f));
        r.add(new Key(".", 0, 1f, "?", "!", "…"));
        r.add(new Key(enterLabel, ENTER, 1.5f));
        return r;
    }

    // --- state
    private final Listener listener;
    private List<List<Key>> rows;
    private int mode = LETTERS;
    private boolean moreSymbols;
    private boolean shift, capsLock;
    private String enterLabel = "↵";
    private final Paint keyPaint = new Paint(Paint.ANTI_ALIAS_FLAG), textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final float density;
    private int bg, keyBg, modKeyBg, pressedBg, fg, accent;
    private Key pressed;
    private Key altKey;            // key whose alternates are shown
    private final List<RectF> altRects = new ArrayList<RectF>();
    private int altIndex = -1;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable longPress, repeat;
    private float[] trailX = new float[512], trailY = new float[512];
    private int trailN = -1;           // -1: no letter press that could become a swipe
    private boolean swiping;
    private final Path trail = new Path();
    private final Paint trailPaint = new Paint(Paint.ANTI_ALIAS_FLAG);

    KeyboardView(Context c, Listener listener) {
        super(c);
        this.listener = listener;
        density = c.getResources().getDisplayMetrics().density;
        textPaint.setTextAlign(Paint.Align.CENTER);
        trailPaint.setStyle(Paint.Style.STROKE);
        trailPaint.setStrokeWidth(5 * density);
        trailPaint.setStrokeCap(Paint.Cap.ROUND);
        trailPaint.setStrokeJoin(Paint.Join.ROUND);
        setTheme(false);
        rows = letters(enterLabel);
    }

    void setTheme(boolean dark) {
        bg = dark ? 0xFF15171C : 0xFFE6E8EE;
        keyBg = dark ? 0xFF2A2E38 : 0xFFFFFFFF;
        modKeyBg = dark ? 0xFF20232B : 0xFFCDD1DA;
        pressedBg = dark ? 0xFF3D4352 : 0xFFB9BECC;
        fg = dark ? 0xFFE9EBF1 : 0xFF15171C;
        accent = dark ? 0xFF8EA2FF : 0xFF2B45D4;
        invalidate();
    }

    void setEnterLabel(String label) {
        enterLabel = label;
        rebuild();
    }

    void setShift(boolean on) {
        if (capsLock) return;
        shift = on;
        invalidate();
    }

    boolean isShift() { return shift || capsLock; }

    /** Key centres of the letter keys, indexed by char (NaN: no key), for decoding swipes. */
    float[][] letterCenters() {
        float[] x = new float[0x100], y = new float[0x100];
        Arrays.fill(x, Float.NaN);
        Arrays.fill(y, Float.NaN);
        if (mode != LETTERS) return new float[][]{x, y};
        for (List<Key> row : rows)
            for (Key k : row)
                if (k.code == 0 && k.label.length() == 1 && Character.isLetter(k.label.charAt(0)) && k.label.charAt(0) < 0x100) {
                    x[k.label.charAt(0)] = k.rect.centerX();
                    y[k.label.charAt(0)] = k.rect.centerY();
                }
        return new float[][]{x, y};
    }

    float keyWidth() { return rows.get(0).get(0).rect.width() + 4 * density; }

    float keyHeight() { return rows.get(0).get(0).rect.height() + 4 * density; }

    void showLetters() {
        mode = LETTERS;
        rebuild();
    }

    private void rebuild() {
        rows = mode == LETTERS ? letters(enterLabel) : symbols(enterLabel, moreSymbols);
        requestLayout();
        layoutKeys(getWidth(), getHeight());
        invalidate();
    }

    @Override
    protected void onMeasure(int w, int h) {
        setMeasuredDimension(MeasureSpec.getSize(w), Math.round(rows.size() * 54 * density + 8 * density));
    }

    @Override
    protected void onSizeChanged(int w, int h, int ow, int oh) { layoutKeys(w, h); }

    private void layoutKeys(int w, int h) {
        if (w == 0 || h == 0) return;
        float gap = 4 * density, rowH = (h - 8 * density) / rows.size();
        float unit = 0;
        for (List<Key> r : rows) {
            float sum = 0;
            for (Key k : r) sum += k.weight;
            unit = Math.max(unit, sum);
        }
        for (int i = 0; i < rows.size(); i++) {
            List<Key> r = rows.get(i);
            float sum = 0;
            for (Key k : r) sum += k.weight;
            float keyW = w / unit;
            float x = (w - sum * keyW) / 2, y = 4 * density + i * rowH;
            for (Key k : r) {
                k.rect.set(x + gap / 2, y + gap / 2, x + k.weight * keyW - gap / 2, y + rowH - gap / 2);
                x += k.weight * keyW;
            }
        }
    }

    @Override
    protected void onDraw(Canvas c) {
        c.drawColor(bg);
        float r = 7 * density;
        for (List<Key> row : rows) {
            for (Key k : row) {
                boolean mod = k.code != 0 && k.code != SPACE;
                keyPaint.setColor(k == pressed ? pressedBg : (k.code == SHIFT && isShift()) ? accent : mod ? modKeyBg : keyBg);
                c.drawRoundRect(k.rect, r, r, keyPaint);
                String label = k.label;
                if (k.code == 0 && isShift()) label = label.toUpperCase();
                textPaint.setColor(k.code == SHIFT && isShift() ? 0xFFFFFFFF : fg);
                boolean small = label.length() > 2;
                textPaint.setTextSize((small ? 14 : 22) * density);
                textPaint.setTypeface(small ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
                if (k.code == ENTER) {                       // hold enter: new line even where enter sends
            longPress = new Runnable() { public void run() { pressed = null; invalidate(); listener.onText("\n"); } };
            handler.postDelayed(longPress, 450);
            return;
        }
        if (k.code == SPACE) { textPaint.setTextSize(13 * density); textPaint.setAlpha(140); }
                c.drawText(label, k.rect.centerX(), k.rect.centerY() - (textPaint.descent() + textPaint.ascent()) / 2, textPaint);
                textPaint.setAlpha(255);
                if (k.alts.length > 0 && k.code == 0 && Character.isLetter(k.label.charAt(0)) && Character.isDigit(k.alts[0].charAt(0))) {
                    textPaint.setTextSize(10 * density);
                    textPaint.setAlpha(120);
                    c.drawText(k.alts[0], k.rect.right - 7 * density, k.rect.top + 12 * density, textPaint);
                    textPaint.setAlpha(255);
                }
            }
        }
        if (swiping && trailN > 1) {
            trailPaint.setColor(accent);
            trailPaint.setAlpha(170);
            trail.reset();
            trail.moveTo(trailX[0], trailY[0]);
            for (int i = 1; i < trailN; i++) trail.lineTo(trailX[i], trailY[i]);
            c.drawPath(trail, trailPaint);
        }
        if (altKey != null) {
            for (int i = 0; i < altRects.size(); i++) {
                keyPaint.setColor(i == altIndex ? accent : keyBg);
                c.drawRoundRect(altRects.get(i), r, r, keyPaint);
                textPaint.setColor(i == altIndex ? 0xFFFFFFFF : fg);
                textPaint.setTextSize(22 * density);
                String s = altKey.alts[i];
                if (isShift()) s = s.toUpperCase();
                RectF ar = altRects.get(i);
                c.drawText(s, ar.centerX(), ar.centerY() - (textPaint.descent() + textPaint.ascent()) / 2, textPaint);
            }
        }
    }

    private Key keyAt(float x, float y) {
        Key best = null;
        float bestD = Float.MAX_VALUE;
        for (List<Key> row : rows) {
            for (Key k : row) {
                if (k.rect.contains(x, y)) return k;
                float dx = Math.max(0, Math.max(k.rect.left - x, x - k.rect.right));
                float dy = Math.max(0, Math.max(k.rect.top - y, y - k.rect.bottom));
                float d = dx * dx + dy * dy;
                if (d < bestD) { bestD = d; best = k; }
            }
        }
        return best;
    }

    @Override
    public boolean onTouchEvent(MotionEvent e) {
        float x = e.getX(), y = e.getY();
        switch (e.getActionMasked()) {
            case MotionEvent.ACTION_DOWN: {
                Key k = keyAt(x, y);
                swiping = false;
                trailN = mode == LETTERS && k != null && k.code == 0 && Character.isLetter(k.label.charAt(0)) ? 0 : -1;
                addTrail(x, y);
                down(k);
                return true;
            }
            case MotionEvent.ACTION_POINTER_DOWN: {   // fast two-thumb typing: finish the first key, start the next
                if (swiping) { swiping = false; trailN = -1; pressed = null; invalidate(); return true; }
                trailN = -1;
                if (pressed != null && altKey == null) up();
                int i = e.getActionIndex();
                down(keyAt(e.getX(i), e.getY(i)));
                return true;
            }
            case MotionEvent.ACTION_MOVE:
                if (trailN >= 0 && altKey == null && e.getPointerCount() == 1) {
                    for (int h = 0; h < e.getHistorySize(); h++) addTrail(e.getHistoricalX(h), e.getHistoricalY(h));
                    addTrail(x, y);
                    if (!swiping && Math.hypot(x - trailX[0], y - trailY[0]) > keyWidth() * 0.75f) {
                        swiping = true;                 // the finger left its key: this is a swipe, not a tap
                        cancelTimers();
                        pressed = null;
                    }
                    if (swiping) invalidate();
                }
                if (altKey != null) {
                    int idx = -1;
                    for (int i = 0; i < altRects.size(); i++) {
                        RectF ar = altRects.get(i);
                        if (x >= ar.left && x <= ar.right) idx = i;
                    }
                    if (idx != altIndex) { altIndex = idx; invalidate(); }
                }
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_POINTER_UP:
                if (swiping) {
                    boolean sh = isShift(), caps = capsLock;
                    swiping = false;
                    float[] xs = Arrays.copyOf(trailX, trailN), ys = Arrays.copyOf(trailY, trailN);
                    trailN = -1;
                    if (shift && !capsLock) shift = false;
                    invalidate();
                    listener.onSwipe(xs, ys, sh, caps);
                    return true;
                }
                trailN = -1;
                up();
                return true;
            case MotionEvent.ACTION_CANCEL:
                swiping = false;
                trailN = -1;
                cancelTimers();
                pressed = null;
                altKey = null;
                invalidate();
                return true;
        }
        return true;
    }

    private void down(final Key k) {
        if (k == null) return;
        cancelTimers();
        pressed = k;
        performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP);
        invalidate();
        if (k.code == DELETE) {
            listener.onCode(DELETE);
            repeat = new Runnable() {
                public void run() { listener.onCode(DELETE); handler.postDelayed(this, 50); }
            };
            handler.postDelayed(repeat, 400);
            return;
        }
        if (k.code == ENTER) {                       // hold enter: new line even where enter sends
            longPress = new Runnable() { public void run() { pressed = null; invalidate(); listener.onText("\n"); } };
            handler.postDelayed(longPress, 450);
            return;
        }
        if (k.code == SPACE) {
            longPress = new Runnable() { public void run() { pressed = null; invalidate(); listener.onSwitchLongPress(); } };
            handler.postDelayed(longPress, 500);
            return;
        }
        if (k.alts.length > 0) {
            longPress = new Runnable() { public void run() { showAlts(k); } };
            handler.postDelayed(longPress, 350);
        }
    }

    private void showAlts(Key k) {
        altKey = k;
        altRects.clear();
        float w = k.rect.width(), h = k.rect.height();
        float total = w * k.alts.length;
        float left = Math.max(0, Math.min(k.rect.centerX() - total / 2, getWidth() - total));
        float top = Math.max(0, k.rect.top - h - 4 * density);
        for (int i = 0; i < k.alts.length; i++) altRects.add(new RectF(left + i * w + 2, top, left + (i + 1) * w - 2, top + h));
        altIndex = 0;
        performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
        invalidate();
    }

    private void up() {
        cancelTimers();
        Key k = pressed;
        pressed = null;
        if (altKey != null) {
            if (altIndex >= 0) emitText(altKey.alts[altIndex]);
            altKey = null;
            invalidate();
            return;
        }
        invalidate();
        if (k == null || k.code == DELETE) return;
        switch (k.code) {
            case 0: emitText(k.label); break;
            case SHIFT:
                if (capsLock) { capsLock = false; shift = false; }
                else if (shift) { capsLock = true; }
                else shift = true;
                invalidate();
                break;
            case SYMBOLS: mode = SYMBOLS; moreSymbols = false; rebuild(); break;
            case MORE: moreSymbols = true; rebuild(); break;
            case LETTERS: mode = LETTERS; rebuild(); break;
            case SPACE: listener.onText(" "); break;
            default: listener.onCode(k.code);
        }
    }

    private void emitText(String s) {
        if (isShift() && mode == LETTERS) s = s.toUpperCase();
        listener.onText(s);
        if (shift && !capsLock) { shift = false; invalidate(); }
    }

    private void addTrail(float x, float y) {
        if (trailN < 0) return;
        if (trailN == trailX.length) {
            trailX = Arrays.copyOf(trailX, trailN * 2);
            trailY = Arrays.copyOf(trailY, trailN * 2);
        }
        trailX[trailN] = x;
        trailY[trailN] = y;
        trailN++;
    }

    private void cancelTimers() {
        if (longPress != null) handler.removeCallbacks(longPress);
        if (repeat != null) handler.removeCallbacks(repeat);
        longPress = repeat = null;
    }
}
