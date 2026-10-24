package de.spaceage.feinschliff;

import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.inputmethodservice.InputMethodService;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.ExtractedText;
import android.view.inputmethod.ExtractedTextRequest;
import android.view.inputmethod.InputConnection;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * The Feinschliff keyboard: typing with word suggestions and careful autocorrect, plus an AI bar
 * that rewrites the text of the current field. The bar shows while no word is being typed.
 */
public class FeinschliffIME extends InputMethodService implements KeyboardView.Listener {
    private KeyboardView keys;
    private LinearLayout aiBar;
    private TextView status;
    private Button styleBtn, langBtn, undoBtn;
    private final Handler main = new Handler(Looper.getMainLooper());
    private boolean secret;            // password field: no AI at all
    // every AI change can be undone, one step at a time: the whole field before each change
    private final java.util.ArrayDeque<String[]> history = new java.util.ArrayDeque<>();   // {text before, action}
    private String lastOut, lastSource; // what the AI wrote last time, and from which text
    private int lastTask = -1;
    private boolean busy;              // a request is running
    private LinearLayout styleBar, langBar;   // style or language choices, shown instead of the AI bar
    private long lastSpace;

    private HorizontalScrollView aiScroll;
    private LinearLayout strip;                  // word suggestions, in place of the AI bar
    private final TextView[] slots = new TextView[3];
    private volatile Dictionary dict;
    private boolean typing;                      // a word is being typed with the keys
    private boolean noCorrect;                   // field asks for no autocorrect (URL, e-mail, password ...)
    private String acFrom, acTo, acSep;          // last autocorrect, undone by an immediate backspace
    private String swiped;                       // word just entered by swiping ...
    private boolean swipeSpace;                  // ... with a space put in front of it
    private final List<String> swipeAlts = new ArrayList<>();

    @Override
    public void onCreate() {
        super.onCreate();
        new Thread(new Runnable() {
            public void run() {
                try {
                    final Dictionary d = new Dictionary(FeinschliffIME.this);
                    main.post(new Runnable() { public void run() { dict = d; refresh(); } });
                } catch (Exception ignored) { }
            }
        }).start();
    }

    private boolean dark() {
        return (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
    }

    @Override
    public View onCreateInputView() {
        boolean dark = dark();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(dark ? 0xFF15171C : 0xFFE6E8EE);

        aiBar = new LinearLayout(this);
        aiBar.setGravity(Gravity.CENTER_VERTICAL);
        addAi("Korrigieren", 0);
        addAi("Umformulieren", 1);
        addAi("Übersetzen", 2);
        addAi("Erweitern", 3);
        addAi("Kürzen", 4);
        addAi("Antwort", 5);
        styleBtn = chip("");
        styleBtn.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { showRow(styleBar); }
        });
        langBtn = chip("");
        langBtn.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { showRow(langBar); }
        });
        undoBtn = chip("↶ Rückgängig");
        undoBtn.setVisibility(View.GONE);
        undoBtn.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { undo(); } });
        aiBar.addView(styleBtn);
        aiBar.addView(langBtn);
        aiBar.addView(undoBtn);
        updateChips();
        styleBar = choiceRow(Tasks.STYLE_LABELS, "style", 1);     // tap a style: rewrite right away
        langBar = choiceRow(Tasks.LANGS, "lang", 2);              // tap a language: translate right away
        aiScroll = new HorizontalScrollView(this);
        aiScroll.setHorizontalScrollBarEnabled(false);
        aiScroll.addView(aiBar);
        strip = new LinearLayout(this);
        strip.setVisibility(View.GONE);
        for (int i = 0; i < 3; i++) {
            final TextView t = new TextView(this);
            t.setGravity(Gravity.CENTER);
            t.setTextSize(17);
            t.setSingleLine(true);
            t.setEllipsize(android.text.TextUtils.TruncateAt.END);
            t.setTextColor(dark ? 0xFFE8EAF0 : 0xFF1C1F26);
            if (i == 1) t.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
            t.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { pick((String) t.getTag()); } });
            strip.addView(t, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f));
            slots[i] = t;
        }
        FrameLayout bars = new FrameLayout(this);       // same height for both, so the keys never jump
        bars.addView(aiScroll);
        bars.addView(strip, new FrameLayout.LayoutParams(FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(bars);

        status = new TextView(this);
        status.setTextColor(dark ? 0xFF9BA2B3 : 0xFF5A6070);
        status.setTextSize(13);
        int p = Math.round(8 * getResources().getDisplayMetrics().density);
        status.setPadding(p, 0, p, 0);
        status.setVisibility(View.GONE);
        root.addView(status);

        keys = new KeyboardView(this, this);
        keys.setTheme(dark);
        root.addView(keys);
        return root;
    }

    private Button chip(String text) {
        Button b = new Button(this);
        b.setText(text);
        b.setAllCaps(false);
        b.setTextSize(13);
        b.setMinHeight(0);
        b.setMinimumHeight(0);
        int p = Math.round(6 * getResources().getDisplayMetrics().density);
        b.setPadding(p * 2, p, p * 2, p);
        return b;
    }

    private void addAi(String label, final int task) {
        Button b = chip(label);
        b.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { runAi(task); } });
        aiBar.addView(b);
    }

    private SharedPreferences prefs() { return Panel.prefs(this); }


    /** A row of choices (styles, languages) with ✕ to go back; tapping one saves it and runs the task. */
    private LinearLayout choiceRow(final String[] labels, final String pref, final int task) {
        LinearLayout row = new LinearLayout(this);
        row.setGravity(Gravity.CENTER_VERTICAL);
        Button back = chip("✕");
        back.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { showRow(aiBar); } });
        row.addView(back);
        for (int i = 0; i < labels.length; i++) {
            final int choice = i;
            Button b = chip(labels[i]);
            b.setOnClickListener(new View.OnClickListener() {
                public void onClick(View v) {
                    if (busy) return;
                    prefs().edit().putInt(pref, choice).apply();
                    updateChips();
                    runAi(task);
                }
            });
            row.addView(b);
        }
        Button undo = chip("↶");
        undo.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { undo(); } });
        row.addView(undo);
        return row;
    }

    /** Shows the AI bar, the style row or the language row. */
    private void showRow(LinearLayout row) {
        if (aiScroll == null || aiScroll.getChildAt(0) == row) return;
        aiScroll.removeAllViews();
        aiScroll.addView(row);
        aiScroll.scrollTo(0, 0);
    }

    private void updateChips() {
        int sel = prefs().getInt("style", 0);
        int lang = prefs().getInt("lang", 0);
        styleBtn.setText("Stil: " + Tasks.STYLE_LABELS[sel] + " ▾");
        langBtn.setText("→ " + Tasks.LANGS[lang] + " ▾");
        mark(styleBar, Tasks.STYLE_LABELS, sel);
        mark(langBar, Tasks.LANGS, lang);
    }

    private void mark(LinearLayout row, String[] labels, int sel) {
        if (row == null) return;
        for (int i = 0; i < labels.length; i++)
            ((Button) row.getChildAt(i + 1)).setText((i == sel ? "✓ " : "") + labels[i]);
    }

    @Override
    public void onStartInputView(EditorInfo info, boolean restarting) {
        super.onStartInputView(info, restarting);
        if (keys == null || info == null) return;
        int cls = info.inputType & InputType.TYPE_MASK_CLASS, var = info.inputType & InputType.TYPE_MASK_VARIATION;
        secret = (cls == InputType.TYPE_CLASS_TEXT && (var == InputType.TYPE_TEXT_VARIATION_PASSWORD
                || var == InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD || var == InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD))
                || (cls == InputType.TYPE_CLASS_NUMBER && var == InputType.TYPE_NUMBER_VARIATION_PASSWORD);
        aiBar.setVisibility(secret ? View.GONE : View.VISIBLE);
        noCorrect = secret || (cls == InputType.TYPE_CLASS_TEXT && (var == InputType.TYPE_TEXT_VARIATION_URI
                || var == InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS || var == InputType.TYPE_TEXT_VARIATION_WEB_EMAIL_ADDRESS
                || (info.inputType & InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS) != 0)) || cls != InputType.TYPE_CLASS_TEXT
                || !prefs().getBoolean("autocorrect", true);
        typing = false;
        acFrom = null;
        swiped = null;
        if (!restarting) { history.clear(); lastOut = null; }   // a different field: its own undo steps
        undoBtn.setVisibility(history.isEmpty() ? View.GONE : View.VISIBLE);
        status.setVisibility(View.GONE);
        showRow(aiBar);
        keys.setTheme(dark());
        keys.showLetters();
        int action = info.imeOptions & EditorInfo.IME_MASK_ACTION;
        boolean multiLine = (info.inputType & InputType.TYPE_TEXT_FLAG_MULTI_LINE) != 0;
        String label = "↵";
        if (!multiLine && (info.imeOptions & EditorInfo.IME_FLAG_NO_ENTER_ACTION) == 0) {
            if (action == EditorInfo.IME_ACTION_SEND) label = "Senden";
            else if (action == EditorInfo.IME_ACTION_SEARCH || action == EditorInfo.IME_ACTION_GO) label = "Los";
            else if (action == EditorInfo.IME_ACTION_NEXT) label = "Weiter";
            else if (action == EditorInfo.IME_ACTION_DONE) label = "Fertig";
        }
        keys.setEnterLabel(label);
        autoCaps();
        refresh();
    }

    @Override
    public void onFinishInputView(boolean finishing) {
        super.onFinishInputView(finishing);
        if (dict != null) dict.save();
    }

    @Override
    public void onUpdateSelection(int oldSelStart, int oldSelEnd, int newSelStart, int newSelEnd, int candStart, int candEnd) {
        super.onUpdateSelection(oldSelStart, oldSelEnd, newSelStart, newSelEnd, candStart, candEnd);
        if (newSelStart != newSelEnd) typing = false;
        refresh();
    }

    // --- suggestions

    /** The letters right before the cursor, or "" (also when the cursor sits inside a word). */
    private String currentWord() {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return "";
        CharSequence before = ic.getTextBeforeCursor(48, 0), after = ic.getTextAfterCursor(1, 0);
        if (before == null) return "";
        if (after != null && after.length() > 0 && Character.isLetter(after.charAt(0))) return "";
        int i = before.length();
        while (i > 0 && (Character.isLetter(before.charAt(i - 1)) || (before.charAt(i - 1) == '\'' && i > 1
                && i < before.length() && Character.isLetter(before.charAt(i - 2))))) i--;
        return before.subSequence(i, before.length()).toString();
    }

    /**
     * The word before the cursor, skipping the word being typed if skipCurrent; "<s>" at the start of a
     * sentence, null when unclear (a number, a bracket ...). Gives suggestions and swipes their context.
     */
    private String previousWord(boolean skipCurrent) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return null;
        CharSequence t = ic.getTextBeforeCursor(80, 0);
        if (t == null) return null;
        int i = t.length();
        if (skipCurrent) while (i > 0 && (Character.isLetter(t.charAt(i - 1)) || t.charAt(i - 1) == '\'')) i--;
        while (i > 0 && (t.charAt(i - 1) == ' ' || t.charAt(i - 1) == ',')) i--;
        if (i == 0 || ".!?\n".indexOf(t.charAt(i - 1)) >= 0) return "<s>";
        int end = i;
        while (i > 0 && (Character.isLetter(t.charAt(i - 1)) || t.charAt(i - 1) == '\'')) i--;
        return end > i ? t.subSequence(i, end).toString() : null;
    }

    /** Gives a suggestion the case of what was typed: "Haus" at a sentence start, "HAUS" when shouting. */
    private static String matchCase(String typed, String word) {
        if (typed.isEmpty() || word.isEmpty()) return word;
        if (typed.length() > 1 && typed.equals(typed.toUpperCase(Locale.GERMAN)) && !typed.equals(typed.toLowerCase(Locale.GERMAN)))
            return word.toUpperCase(Locale.GERMAN);
        if (Character.isUpperCase(typed.charAt(0))) return word.substring(0, 1).toUpperCase(Locale.GERMAN) + word.substring(1);
        return word;
    }

    /** Shows suggestions while a word is typed, the AI bar otherwise. */
    private void refresh() {
        if (strip == null) return;
        String w = typing && !secret && dict != null ? currentWord() : "";
        if (w.isEmpty()) {
            strip.setVisibility(View.GONE);
            aiScroll.setVisibility(View.VISIBLE);
            return;
        }
        List<String> words = new ArrayList<>();
        dict.setContext(previousWord(true));
        if (swiped != null && swiped.equals(w)) {
            words.addAll(swipeAlts);              // the other words the path could have meant
            showWords(words, w);
            return;
        }
        String fix = noCorrect ? null : dict.autocorrect(w);
        String primary = fix != null ? matchCase(w, fix) : w;
        words.add(primary);
        if (!primary.equals(w)) words.add(w);
        for (Dictionary.Suggestion s : dict.suggest(w, 6)) {
            String x = matchCase(w, s.word);
            if (!words.contains(x)) words.add(x);
        }
        showWords(words, w);
    }

    private void showWords(List<String> words, String w) {
        // middle: what space will produce; left and right: the alternatives
        String[] order = {words.size() > 1 ? words.get(1) : null, words.get(0), words.size() > 2 ? words.get(2) : null};
        for (int i = 0; i < 3; i++) {
            String x = order[i];
            boolean unknown = x != null && x.equals(w) && !dict.isKnown(w);
            slots[i].setText(x == null ? "" : unknown ? "„" + x + "“" : x);
            slots[i].setTag(x);
        }
        aiScroll.setVisibility(View.INVISIBLE);
        strip.setVisibility(View.VISIBLE);
    }

    /** A tapped suggestion replaces the word being typed. */
    private void pick(String word) {
        InputConnection ic = getCurrentInputConnection();
        if (word == null || ic == null || dict == null) return;
        String w = currentWord();
        if (word.equals(w) && !dict.isKnown(w)) dict.learn(w);      // tapped "„word“": keep this spelling
        dict.used(word, previousWord(true));
        ic.beginBatchEdit();
        ic.deleteSurroundingText(w.length(), 0);
        ic.commitText(word + " ", 1);
        ic.endBatchEdit();
        typing = false;
        acFrom = null;
        swiped = null;
        autoCaps();
        refresh();
    }

    // --- swipe

    @Override
    public void onSwipe(float[] xs, float[] ys, boolean shift, boolean caps) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null || keys == null) return;
        if (dict == null) { say("Wörterbuch lädt noch, gleich nochmal wischen …"); return; }
        float[][] c = keys.letterCenters();
        if (afterSwipe()) dict.used(swiped, previousWord(true));   // the previous swiped word is finished now
        dict.setContext(previousWord(false));
        List<Dictionary.Suggestion> found = dict.swipe(xs, ys, c[0], c[1], keys.keyWidth(), keys.keyHeight(), 4);
        if (found.isEmpty()) { say("Kein passendes Wort erkannt."); return; }
        say(null);
        swipeAlts.clear();
        for (Dictionary.Suggestion s : found) {
            String x = caps ? s.word.toUpperCase(Locale.GERMAN)
                    : shift ? s.word.substring(0, 1).toUpperCase(Locale.GERMAN) + s.word.substring(1) : s.word;
            if (!swipeAlts.contains(x)) swipeAlts.add(x);
        }
        String word = swipeAlts.get(0);
        CharSequence before = ic.getTextBeforeCursor(1, 0);
        swipeSpace = before != null && before.length() == 1 && !Character.isWhitespace(before.charAt(0))
                && "([{„\"'/@#-".indexOf(before.charAt(0)) < 0;       // words get a space between them automatically
        ic.beginBatchEdit();
        CharSequence sel = ic.getSelectedText(0);
        if (sel != null && sel.length() > 0) { ic.commitText("", 1); swipeSpace = false; }
        ic.commitText(swipeSpace ? " " + word : word, 1);
        ic.endBatchEdit();
        swiped = word;
        typing = true;
        acFrom = null;
        autoCaps();
        refresh();
    }

    /** True if the cursor stands right after the word just swiped. */
    private boolean afterSwipe() { return swiped != null && swiped.equals(currentWord()); }

    /** Called before a space or punctuation mark: learns the finished word and maybe corrects it. */
    private void finishWord(InputConnection ic, String sep) {
        String w = currentWord();
        typing = false;
        acFrom = null;
        if (w.isEmpty() || dict == null || secret) return;
        String fix = noCorrect ? null : dict.autocorrect(w);
        if (fix != null) {
            fix = matchCase(w, fix);
            ic.deleteSurroundingText(w.length(), 0);
            ic.commitText(fix, 1);
            acFrom = w;
            acTo = fix;
            acSep = sep;
            dict.used(fix, previousWord(true));
        } else {
            dict.used(w, previousWord(true));
        }
    }

    /** Backspace right after an autocorrect brings back what was typed, and remembers it. */
    private boolean revertAutocorrect(InputConnection ic) {
        if (acFrom == null) return false;
        String done = acTo + acSep;
        CharSequence before = ic.getTextBeforeCursor(done.length(), 0);
        String from = acFrom;
        acFrom = null;
        if (before == null || !before.toString().equals(done)) return false;
        ic.beginBatchEdit();
        ic.deleteSurroundingText(done.length(), 0);
        ic.commitText(from + acSep, 1);
        ic.endBatchEdit();
        dict.learn(from);
        return true;
    }

    private void autoCaps() {
        InputConnection ic = getCurrentInputConnection();
        EditorInfo info = getCurrentInputEditorInfo();
        if (ic == null || info == null || keys == null) return;
        keys.setShift(info.inputType != InputType.TYPE_NULL && ic.getCursorCapsMode(info.inputType) != 0);
    }

    // --- typing

    @Override
    public void onText(String text) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;
        boolean letter = text.length() > 0 && Character.isLetter(text.codePointAt(0));
        if (letter && afterSwipe()) {             // typing after a swiped word starts a new word
            ic.beginBatchEdit();
            finishWord(ic, " ");
            acFrom = null;
            ic.commitText(" ", 1);
            ic.endBatchEdit();
        }
        swiped = null;
        if (!letter && text.length() == 1 && " .,!?;:)\"".indexOf(text.charAt(0)) >= 0) {
            ic.beginBatchEdit();
            finishWord(ic, text);
            ic.endBatchEdit();
        } else {
            acFrom = null;
            typing = letter || (typing && "'".equals(text));
        }
        if (" ".equals(text)) {
            long now = System.currentTimeMillis();
            CharSequence before = ic.getTextBeforeCursor(2, 0);
            if (now - lastSpace < 400 && before != null && before.length() == 2 && before.charAt(1) == ' '
                    && Character.isLetterOrDigit(before.charAt(0))) {
                ic.deleteSurroundingText(1, 0);   // double space -> ". "
                ic.commitText(". ", 1);
                lastSpace = 0;
                autoCaps();
                return;
            }
            lastSpace = now;
        }
        ic.commitText(text, 1);
        autoCaps();
    }

    @Override
    public void onCode(int code) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;
        if (code != KeyboardView.DELETE && code != KeyboardView.SHIFT && code != KeyboardView.SYMBOLS
                && code != KeyboardView.LETTERS && code != KeyboardView.MORE) acFrom = null;
        if (code == KeyboardView.DELETE && afterSwipe()) {   // backspace takes back the whole swiped word
            CharSequence before = ic.getTextBeforeCursor(swiped.length() + 1, 0);
            boolean space = swipeSpace && before != null && before.length() == swiped.length() + 1 && before.charAt(0) == ' ';
            ic.deleteSurroundingText(swiped.length() + (space ? 1 : 0), 0);
            swiped = null;
            typing = false;
            autoCaps();
            refresh();
            return;
        }
        if (code != KeyboardView.SHIFT) swiped = null;
        if (code == KeyboardView.DELETE) {
            if (revertAutocorrect(ic)) { typing = false; autoCaps(); return; }
            typing = true;
            CharSequence sel = ic.getSelectedText(0);
            if (sel != null && sel.length() > 0) ic.commitText("", 1);
            else {
                CharSequence before = ic.getTextBeforeCursor(2, 0);
                int n = before != null && before.length() == 2 && Character.isSurrogatePair(before.charAt(0), before.charAt(1)) ? 2 : 1;
                ic.deleteSurroundingText(n, 0);
            }
            autoCaps();
        } else if (code == KeyboardView.ENTER) {
            ic.beginBatchEdit();
            finishWord(ic, "\n");
            acFrom = null;                 // no revert across a line break or a sent message
            ic.endBatchEdit();
            EditorInfo info = getCurrentInputEditorInfo();
            int action = info == null ? EditorInfo.IME_ACTION_NONE : info.imeOptions & EditorInfo.IME_MASK_ACTION;
            boolean multiLine = info != null && (info.inputType & InputType.TYPE_TEXT_FLAG_MULTI_LINE) != 0;
            if (!multiLine && info != null && (info.imeOptions & EditorInfo.IME_FLAG_NO_ENTER_ACTION) == 0
                    && action != EditorInfo.IME_ACTION_NONE && action != EditorInfo.IME_ACTION_UNSPECIFIED) {
                ic.performEditorAction(action);
            } else {
                ic.commitText("\n", 1);
            }
            autoCaps();
        } else if (code == KeyboardView.SWITCH) {
            if (android.os.Build.VERSION.SDK_INT < 28 || !switchToNextInputMethod(false)) onSwitchLongPress();
        }
    }

    @Override
    public void onSwitchLongPress() {
        InputMethodManager imm = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        imm.showInputMethodPicker();
    }

    // --- AI

    private static final class Range {
        int start, end;
        String text;
    }

    /** The text the AI should work on: the selection, or else the whole field. */
    private Range target() {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return null;
        ExtractedText et = ic.getExtractedText(new ExtractedTextRequest(), 0);
        if (et == null || et.text == null) return null;
        Range r = new Range();
        int s = Math.min(et.selectionStart, et.selectionEnd), e = Math.max(et.selectionStart, et.selectionEnd);
        if (s >= 0 && e > s) {
            r.start = et.startOffset + s;
            r.end = et.startOffset + e;
            r.text = et.text.subSequence(s, e).toString();
        } else {
            r.start = et.startOffset;
            r.end = et.startOffset + et.text.length();
            r.text = et.text.toString();
        }
        return r;
    }

    private void say(String msg) {
        status.setText(msg);
        status.setVisibility(msg == null ? View.GONE : View.VISIBLE);
    }

    private void runAi(int task) {
        if (secret || busy) return;
        final String key = prefs().getString("key", "");
        if (key.trim().isEmpty()) { say("Trage zuerst deinen API-Schlüssel in der Feinschliff-App ein."); return; }
        final Range r = target();
        if (r == null || r.text.trim().isEmpty()) { say("Kein Text im Feld."); return; }
        final String source = (task == 1 || task == 2) && task == lastTask && r.text.equals(lastOut) && lastSource != null
                ? lastSource : r.text;  // another style or language: start again from the original, not from the last result
        final String before = fieldText();
        r.text = source;
        final String prompt = Tasks.prompt(task, prefs().getInt("style", 0), prefs().getInt("lang", 0), r.text, null);
        say("Denkt nach …");
        busy = true;
        new Thread(new Runnable() {
            public void run() {
                String out = null, err = null;
                try { out = Claude.ask(key, prompt, null); } catch (Exception e) { err = e.getMessage() != null ? e.getMessage() : "Keine Verbindung."; }
                final String o = out, er = err;
                main.post(new Runnable() {
                    public void run() {
                        busy = false;
                        if (er != null) { say(er); return; }
                        typing = false;
                        swiped = null;
                        if (before != null) {
                            history.push(new String[]{before, Tasks.NAMES[task]});
                            while (history.size() > 30) history.removeLast();
                        }
                        replace(r, o);
                        lastOut = o;
                        lastSource = source;
                        lastTask = task;
                        updateUndo();
                        say(null);
                    }
                });
            }
        }).start();
    }

    private void replace(Range r, String text) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;
        ic.beginBatchEdit();
        ic.setSelection(r.start, r.end);
        ic.commitText(text, 1);
        ic.endBatchEdit();
    }

    /** The whole text of the field, or null if the app doesn't tell. */
    private String fieldText() {
        InputConnection ic = getCurrentInputConnection();
        ExtractedText et = ic == null ? null : ic.getExtractedText(new ExtractedTextRequest(), 0);
        return et == null || et.text == null || et.startOffset != 0 ? null : et.text.toString();
    }

    private void updateUndo() {
        undoBtn.setText("↶ Rückgängig" + (history.size() > 1 ? " (" + history.size() + ")" : ""));
        undoBtn.setVisibility(history.isEmpty() ? View.GONE : View.VISIBLE);
    }

    /** Puts the field back as it was before the last AI change; tap again for the one before. */
    private void undo() {
        InputConnection ic = getCurrentInputConnection();
        String now = fieldText();
        if (history.isEmpty() || ic == null || now == null) { say(history.isEmpty() ? "Nichts mehr rückgängig zu machen." : null); return; }
        String[] step = history.pop();
        Range r = new Range();
        r.start = 0;
        r.end = now.length();
        replace(r, step[0]);
        lastOut = null;
        say("Rückgängig: Text vor „" + step[1] + "“");
        updateUndo();
    }
}
