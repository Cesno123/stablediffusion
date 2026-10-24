package de.spaceage.feinschliff;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.util.Base64;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;

/** The app screen: text in (typed, shared or read from a photo), one task, text out. */
public class MainActivity extends Activity {
    private static final int PICK_PHOTO = 1;
    private EditText input;
    private Panel panel;

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout root = Panel.column(this);
        input = new EditText(this);
        panel = new Panel(this, new Panel.Source() { public String text() { return input.getText().toString(); } });
        int pad = panel.dp(16);
        root.setPadding(pad, pad, pad, pad * 2);

        TextView title = new TextView(this);
        title.setText("Feinschliff");
        title.setTextSize(30);
        title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        root.addView(title);
        TextView hint = new TextView(this);
        hint.setText("Text einfügen oder Foto lesen lassen, Aufgabe wählen, „Los“. Tipp: Markiere Text in einer beliebigen App und wähle im Menü „Feinschliff“.");
        hint.setAlpha(0.7f);
        root.addView(hint);

        input.setHint("Dein Text");
        input.setMinLines(5);
        input.setGravity(android.view.Gravity.TOP);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE | InputType.TYPE_TEXT_FLAG_CAP_SENTENCES);
        input.setText(Panel.prefs(this).getString("draft", ""));
        root.addView(input);

        LinearLayout row = new LinearLayout(this);
        Button photo = new Button(this);
        photo.setText("Text aus Foto");
        photo.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Intent i = new Intent(Intent.ACTION_GET_CONTENT).setType("image/*");
                startActivityForResult(Intent.createChooser(i, "Foto wählen"), PICK_PHOTO);
            }
        });
        Button clear = new Button(this);
        clear.setText("Leeren");
        clear.setOnClickListener(new View.OnClickListener() { public void onClick(View v) { input.setText(""); } });
        Button use = new Button(this);
        use.setText("Ergebnis übernehmen");
        use.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { input.setText(panel.result.getText()); }
        });
        row.addView(photo);
        row.addView(clear);
        root.addView(row);
        root.addView(panel.root);
        root.addView(use);

        // keyboard setup
        root.addView(panel.label("Feinschliff-Tastatur"));
        Button enableKb = new Button(this);
        enableKb.setText("1. Tastatur einschalten");
        enableKb.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) { startActivity(new Intent(android.provider.Settings.ACTION_INPUT_METHOD_SETTINGS)); }
        });
        Button pickKb = new Button(this);
        pickKb.setText("2. Als Tastatur auswählen");
        pickKb.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                ((android.view.inputmethod.InputMethodManager) getSystemService(INPUT_METHOD_SERVICE)).showInputMethodPicker();
            }
        });
        root.addView(enableKb);
        root.addView(pickKb);
        final android.widget.CheckBox autocorrect = new android.widget.CheckBox(this);
        autocorrect.setText("Autokorrektur (Rücktaste direkt danach macht sie rückgängig)");
        autocorrect.setChecked(Panel.prefs(this).getBoolean("autocorrect", true));
        autocorrect.setOnCheckedChangeListener(new android.widget.CompoundButton.OnCheckedChangeListener() {
            public void onCheckedChanged(android.widget.CompoundButton b, boolean on) {
                Panel.prefs(MainActivity.this).edit().putBoolean("autocorrect", on).apply();
            }
        });
        root.addView(autocorrect);
        Button location = new Button(this);
        location.setText("Standort erlauben (für „📌 Mein Standort“)");
        location.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                requestPermissions(new String[]{android.Manifest.permission.ACCESS_FINE_LOCATION,
                        android.Manifest.permission.ACCESS_COARSE_LOCATION}, 7);
            }
        });
        root.addView(location);

        // settings
        root.addView(panel.label("API-Schlüssel (von console.anthropic.com, bleibt nur auf diesem Handy)"));
        final EditText key = new EditText(this);
        key.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        key.setHint("sk-ant-…");
        key.setText(Panel.prefs(this).getString("key", ""));
        root.addView(key);
        Button saveKey = new Button(this);
        saveKey.setText("Schlüssel speichern");
        saveKey.setOnClickListener(new View.OnClickListener() {
            public void onClick(View v) {
                Panel.prefs(MainActivity.this).edit().putString("key", key.getText().toString().trim()).apply();
                String k = key.getText().toString().trim();
                android.widget.Toast.makeText(MainActivity.this, k.isEmpty() ? "Schlüssel gelöscht."
                        : k.startsWith("sk-ant-") ? "Schlüssel gespeichert ✓" : "Gespeichert – aber ein Schlüssel beginnt normalerweise mit sk-ant-",
                        android.widget.Toast.LENGTH_LONG).show();
            }
        });
        root.addView(saveKey);
        TextView model = new TextView(this);
        model.setText("Modell: " + Claude.MODEL + " · Version 1.9");
        model.setAlpha(0.5f);
        root.addView(model);

        ScrollView sv = new ScrollView(this);
        sv.addView(root);
        setContentView(sv);
        handleShare(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handleShare(intent);
    }

    @Override
    protected void onPause() {
        super.onPause();
        Panel.prefs(this).edit().putString("draft", input.getText().toString()).apply();
    }

    private void handleShare(Intent i) {
        if (i == null || !Intent.ACTION_SEND.equals(i.getAction())) return;
        String text = i.getStringExtra(Intent.EXTRA_TEXT);
        Uri img = i.getParcelableExtra(Intent.EXTRA_STREAM);
        if (text != null) input.setText(text);
        else if (img != null) readPhoto(img);
    }

    @Override
    protected void onActivityResult(int req, int res, Intent data) {
        super.onActivityResult(req, res, data);
        if (req == PICK_PHOTO && res == RESULT_OK && data != null && data.getData() != null) readPhoto(data.getData());
    }

    private void readPhoto(Uri uri) {
        String b64;
        try { b64 = jpegBase64(uri); } catch (Exception e) { panel.status.setText("Das Foto ließ sich nicht öffnen."); return; }
        panel.run(Tasks.OCR, b64, new Panel.Done() {
            public void done(String text) {
                if (text.trim().equals("KEIN TEXT")) { panel.status.setText("Auf dem Foto wurde kein Text gefunden."); return; }
                input.setText(text);
                panel.status.setText("Text aus dem Foto übernommen. Jetzt eine Aufgabe wählen.");
            }
        });
    }

    /** Loads the image scaled to at most ~1568 px on the long side and encodes it as JPEG base64. */
    private String jpegBase64(Uri uri) throws Exception {
        BitmapFactory.Options o = new BitmapFactory.Options();
        o.inJustDecodeBounds = true;
        InputStream in = getContentResolver().openInputStream(uri);
        BitmapFactory.decodeStream(in, null, o);
        in.close();
        int sample = 1;
        while (Math.max(o.outWidth, o.outHeight) / (sample * 2) >= 1568) sample *= 2;
        BitmapFactory.Options o2 = new BitmapFactory.Options();
        o2.inSampleSize = sample;
        in = getContentResolver().openInputStream(uri);
        Bitmap bmp = BitmapFactory.decodeStream(in, null, o2);
        in.close();
        if (bmp == null) throw new Exception("decode");
        float scale = 1568f / Math.max(bmp.getWidth(), bmp.getHeight());
        if (scale < 1) bmp = Bitmap.createScaledBitmap(bmp, Math.round(bmp.getWidth() * scale), Math.round(bmp.getHeight() * scale), true);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.JPEG, 85, out);
        return Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP);
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        boolean ok = false;
        for (int r : results) ok |= r == android.content.pm.PackageManager.PERMISSION_GRANTED;
        android.widget.Toast.makeText(this, ok ? "Standort erlaubt ✓" : "Standort nicht erlaubt.", android.widget.Toast.LENGTH_LONG).show();
    }
}
