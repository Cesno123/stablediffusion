package de.spaceage.feinschliff;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** "Feinschliff" in the text-selection menu of other apps: rewrites the selected text and puts it back. */
public class ProcessTextActivity extends Activity {
    @Override
    protected void onCreate(Bundle saved) {
        boolean night = (getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK)
                == android.content.res.Configuration.UI_MODE_NIGHT_YES;
        setTheme(night ? android.R.style.Theme_DeviceDefault_Dialog_MinWidth : android.R.style.Theme_DeviceDefault_Light_Dialog_MinWidth);
        super.onCreate(saved);
        CharSequence sel = getIntent().getCharSequenceExtra(Intent.EXTRA_PROCESS_TEXT);
        final String selected = sel == null ? "" : sel.toString();
        final boolean readOnly = getIntent().getBooleanExtra(Intent.EXTRA_PROCESS_TEXT_READONLY, false);

        final Panel panel = new Panel(this, new Panel.Source() { public String text() { return selected; } });
        final Button replace = new Button(this);
        replace.setText(readOnly ? "Kopieren und schließen" : "Ersetzen");
        replace.setEnabled(false);
        replace.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                String out = panel.result.getText().toString();
                if (readOnly) { Panel.copyText(ProcessTextActivity.this, out); finish(); return; }
                setResult(RESULT_OK, new Intent().putExtra(Intent.EXTRA_PROCESS_TEXT, out));
                finish();
            }
        });
        LinearLayout root = Panel.column(this);
        int pad = panel.dp(16);
        root.setPadding(pad, pad, pad, pad);
        TextView preview = new TextView(this);
        preview.setText(selected.length() > 300 ? selected.substring(0, 300) + " …" : selected);
        preview.setAlpha(0.7f);
        preview.setMaxLines(6);
        root.addView(preview);
        root.addView(panel.root);
        root.addView(replace);
        ScrollView sv = new ScrollView(this);
        sv.addView(root);
        setContentView(sv);
        setTitle("Feinschliff");
        getWindow().setLayout(android.view.ViewGroup.LayoutParams.MATCH_PARENT, android.view.ViewGroup.LayoutParams.WRAP_CONTENT);

        // enable "Ersetzen" once an answer is there
        panel.result.addTextChangedListener(new android.text.TextWatcher() {
            public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            public void onTextChanged(CharSequence s, int a, int b, int c) {}
            public void afterTextChanged(android.text.Editable s) { replace.setEnabled(s.length() > 0); }
        });
    }
}
