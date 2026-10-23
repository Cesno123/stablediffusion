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
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;

/** The Feinschliff keyboard: typing plus an AI bar that rewrites the text of the current field. */
public class FeinschliffIME extends InputMethodService implements KeyboardView.Listener {
    private KeyboardView keys;
    private LinearLayout aiBar;
    private TextView status;
    private Button styleBtn, langBtn, undoBtn;
    private final Handler main = new Handler(Looper.getMainLooper());
    private boolean secret;            // password field: no AI at all
    private String undoText;           // text before the last AI change ...
    private int undoStart, undoLen;    // ... and where the AI's text now stands
    private long lastSpace;

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
            public void onClick(View v) { cycle("style", Tasks.STYLE_LABELS.length); updateChips(); }
        });
        langBtn = chip("");
        langBtn.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { cycle("lang", Tasks.LANGS.length); updateChips(); }
        });
        undoBtn = chip("↶ Rückgängig");
        undoBtn.setVisibility(View.GONE);
        undoBtn.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { undo(); } });
        aiBar.addView(styleBtn);
        aiBar.addView(langBtn);
        aiBar.addView(undoBtn);
        updateChips();
        HorizontalScrollView scroll = new HorizontalScrollView(this);
        scroll.setHorizontalScrollBarEnabled(false);
        scroll.addView(aiBar);
        root.addView(scroll);

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

    private void cycle(String key, int n) { prefs().edit().putInt(key, (prefs().getInt(key, 0) + 1) % n).apply(); }

    private void updateChips() {
        styleBtn.setText("Stil: " + Tasks.STYLE_LABELS[prefs().getInt("style", 0)]);
        langBtn.setText("→ " + Tasks.LANGS[prefs().getInt("lang", 0)]);
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
        undoText = null;
        undoBtn.setVisibility(View.GONE);
        status.setVisibility(View.GONE);
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
        if (code == KeyboardView.DELETE) {
            CharSequence sel = ic.getSelectedText(0);
            if (sel != null && sel.length() > 0) ic.commitText("", 1);
            else {
                CharSequence before = ic.getTextBeforeCursor(2, 0);
                int n = before != null && before.length() == 2 && Character.isSurrogatePair(before.charAt(0), before.charAt(1)) ? 2 : 1;
                ic.deleteSurroundingText(n, 0);
            }
            autoCaps();
        } else if (code == KeyboardView.ENTER) {
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
        if (secret) return;
        final String key = prefs().getString("key", "");
        if (key.trim().isEmpty()) { say("Trage zuerst deinen API-Schlüssel in der Feinschliff-App ein."); return; }
        final Range r = target();
        if (r == null || r.text.trim().isEmpty()) { say("Kein Text im Feld."); return; }
        final String prompt = Tasks.prompt(task, prefs().getInt("style", 0), prefs().getInt("lang", 0), r.text, null);
        say("Denkt nach …");
        new Thread(new Runnable() {
            public void run() {
                String out = null, err = null;
                try { out = Claude.ask(key, prompt, null); } catch (Exception e) { err = e.getMessage() != null ? e.getMessage() : "Keine Verbindung."; }
                final String o = out, er = err;
                main.post(new Runnable() {
                    public void run() {
                        if (er != null) { say(er); return; }
                        replace(r, o);
                        undoText = r.text;
                        undoStart = r.start;
                        undoLen = o.length();
                        undoBtn.setVisibility(View.VISIBLE);
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

    private void undo() {
        if (undoText == null) return;
        Range r = new Range();
        r.start = undoStart;
        r.end = undoStart + undoLen;
        replace(r, undoText);
        undoText = null;
        undoBtn.setVisibility(View.GONE);
    }
}
