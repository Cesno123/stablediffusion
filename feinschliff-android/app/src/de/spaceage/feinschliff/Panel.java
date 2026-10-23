package de.spaceage.feinschliff;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

/** The task controls shared by the app screen and the text-selection dialog: task, style, language, go, result. */
final class Panel {
    final Activity a;
    final LinearLayout root;
    final Spinner task, style, lang;
    final EditText context;
    final Button go, copy, again;
    final TextView result, status;
    final ProgressBar busy;
    private String lastPrompt, lastImage;
    private final Handler main = new Handler(Looper.getMainLooper());

    interface Source { String text(); }
    private final Source source;

    Panel(Activity a, Source source) {
        this.a = a;
        this.source = source;
        root = column(a);
        context = new EditText(a);
        context.setHint("Zusammenhang (optional), z. B. Nachricht an meinen Chef");
        context.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        task = spinner(Tasks.NAMES);
        style = spinner(Tasks.STYLE_LABELS);
        lang = spinner(Tasks.LANGS);
        root.addView(label("Aufgabe"));
        root.addView(task);
        root.addView(label("Stil"));
        root.addView(style);
        root.addView(label("Sprache"));
        root.addView(lang);
        root.addView(context);
        go = new Button(a);
        go.setText("Los");
        root.addView(go);
        busy = new ProgressBar(a);
        busy.setVisibility(View.GONE);
        root.addView(busy);
        status = new TextView(a);
        root.addView(status);
        result = new TextView(a);
        result.setTextIsSelectable(true);
        result.setTextSize(17);
        result.setPadding(0, dp(8), 0, dp(8));
        root.addView(result);
        LinearLayout row = new LinearLayout(a);
        copy = new Button(a);
        copy.setText("Kopieren");
        again = new Button(a);
        again.setText("Andere Variante");
        row.addView(copy);
        row.addView(again);
        root.addView(row);
        copy.setEnabled(false);
        again.setEnabled(false);

        SharedPreferences p = prefs(a);
        task.setSelection(p.getInt("task", 0));
        style.setSelection(p.getInt("style", 0));
        lang.setSelection(p.getInt("lang", 0));
        task.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onItemSelected(AdapterView<?> v, View view, int pos, long id) { refresh(); }
            public void onNothingSelected(AdapterView<?> v) {}
        });
        go.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                String text = Panel.this.source.text();
                if (text.trim().isEmpty()) { status.setText("Füge zuerst einen Text ein."); return; }
                prefs(Panel.this.a).edit().putInt("task", task.getSelectedItemPosition())
                        .putInt("style", style.getSelectedItemPosition()).putInt("lang", lang.getSelectedItemPosition()).apply();
                run(Tasks.prompt(task.getSelectedItemPosition(), style.getSelectedItemPosition(),
                        lang.getSelectedItemPosition(), text, context.getText().toString()), null, null);
            }
        });
        again.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { if (lastPrompt != null) run(lastPrompt + "\n(Schreibe eine andere Variante als zuvor.)", lastImage, null); }
        });
        copy.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { copyText(Panel.this.a, result.getText().toString()); }
        });
        refresh();
    }

    void refresh() {
        int t = task.getSelectedItemPosition();
        style.setEnabled(Tasks.usesStyle(t));
        lang.setEnabled(Tasks.usesLang(t));
    }

    interface Done { void done(String text); }

    /** Runs one request off the main thread; done (optional) receives the answer instead of the result field. */
    void run(final String prompt, final String image, final Done done) {
        final String key = prefs(a).getString("key", "");
        if (key.trim().isEmpty()) { status.setText("Trage zuerst deinen API-Schlüssel ein (in der Feinschliff-App ganz unten)."); return; }
        lastPrompt = prompt;
        lastImage = image;
        go.setEnabled(false);
        copy.setEnabled(false);
        again.setEnabled(false);
        busy.setVisibility(View.VISIBLE);
        status.setText(image != null ? "Liest den Text im Foto …" : "Denkt nach …");
        new Thread(new Runnable() {
            public void run() {
                String text = null, error = null;
                try { text = Claude.ask(key, prompt, image); } catch (Exception e) { error = e.getMessage() != null ? e.getMessage() : "Keine Verbindung."; }
                final String t = text, err = error;
                main.post(new Runnable() {
                    public void run() {
                        busy.setVisibility(View.GONE);
                        go.setEnabled(true);
                        if (err != null) { status.setText(err); return; }
                        status.setText("");
                        if (done != null) { done.done(t); return; }
                        result.setText(t);
                        copy.setEnabled(true);
                        again.setEnabled(true);
                        onResult(t);
                    }
                });
            }
        }).start();
    }

    /** Hook for the screens; called with each new answer. */
    void onResult(String text) {}

    // --- small view helpers

    Spinner spinner(String[] items) {
        Spinner s = new Spinner(a);
        ArrayAdapter<String> ad = new ArrayAdapter<String>(a, android.R.layout.simple_spinner_item, items);
        ad.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        s.setAdapter(ad);
        return s;
    }

    TextView label(String text) {
        TextView t = new TextView(a);
        t.setText(text);
        t.setAlpha(0.7f);
        t.setPadding(0, dp(10), 0, 0);
        return t;
    }

    int dp(int v) { return (int) (v * a.getResources().getDisplayMetrics().density + 0.5f); }

    static LinearLayout column(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.VERTICAL);
        return l;
    }

    static SharedPreferences prefs(Context c) { return c.getSharedPreferences("feinschliff", Context.MODE_PRIVATE); }

    static void copyText(Context c, String text) {
        ClipboardManager cm = (ClipboardManager) c.getSystemService(Context.CLIPBOARD_SERVICE);
        cm.setPrimaryClip(ClipData.newPlainText("Feinschliff", text));
        Toast.makeText(c, "Kopiert", Toast.LENGTH_SHORT).show();
    }
}
