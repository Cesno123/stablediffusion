package de.spaceage.feinschliff;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.widget.Toast;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Invisible helper the keyboard starts to pick a picture from the gallery or take one with the camera
 * (a keyboard cannot open those itself). The picture is copied to cache/images and handed back to
 * the keyboard, which inserts it once the app being typed in is back.
 */
public class PickActivity extends Activity {
    static final String MODE = "mode", GALLERY = "gallery", CAMERA = "camera";
    private static final int PICK = 1, SHOOT = 2;
    private String photo;     // file the camera writes to

    @Override
    protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (saved != null) { photo = saved.getString("photo"); return; }   // recreated while the picker was open
        cleanUp();
        try {
            if (CAMERA.equals(getIntent().getStringExtra(MODE))) {
                File f = new File(ImageProvider.dir(this), "foto-" + System.currentTimeMillis() + ".jpg");
                photo = f.getName();
                Uri u = ImageProvider.uriFor(f);
                Intent i = new Intent(MediaStore.ACTION_IMAGE_CAPTURE).putExtra(MediaStore.EXTRA_OUTPUT, u)
                        .addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                i.setClipData(ClipData.newRawUri("", u));
                startActivityForResult(i, SHOOT);
            } else {
                Intent i = Build.VERSION.SDK_INT >= 33 ? new Intent(MediaStore.ACTION_PICK_IMAGES)
                        : new Intent(Intent.ACTION_GET_CONTENT).setType("image/*").addCategory(Intent.CATEGORY_OPENABLE);
                startActivityForResult(i, PICK);
            }
        } catch (ActivityNotFoundException e) {
            Toast.makeText(this, "Keine passende App gefunden.", Toast.LENGTH_LONG).show();
            finish();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        out.putString("photo", photo);
    }

    @Override
    protected void onActivityResult(int request, int result, Intent data) {
        if (request == SHOOT) {
            File f = photo == null ? null : new File(ImageProvider.dir(this), photo);
            if (result == RESULT_OK && f != null && f.length() > 0) FeinschliffIME.imagePicked(f);
            finish();
            return;
        }
        final Uri src = data == null ? null : data.getData();
        if (result != RESULT_OK || src == null) { finish(); return; }
        String mime = getContentResolver().getType(src);
        String ext = "image/png".equals(mime) ? ".png" : "image/gif".equals(mime) ? ".gif" : "image/webp".equals(mime) ? ".webp"
                : "image/heic".equals(mime) || "image/heif".equals(mime) ? ".heic" : ".jpg";
        final File f = new File(ImageProvider.dir(this), "bild-" + System.currentTimeMillis() + ext);
        new Thread(new Runnable() {                // pictures can be large: copy off the main thread
            public void run() {
                boolean ok = false;
                try (InputStream in = getContentResolver().openInputStream(src); OutputStream out = new FileOutputStream(f)) {
                    byte[] buf = new byte[1 << 16];
                    int n;
                    while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
                    ok = true;
                } catch (Exception ignored) { }
                final boolean done = ok;
                runOnUiThread(new Runnable() {
                    public void run() {
                        if (done) FeinschliffIME.imagePicked(f);
                        else Toast.makeText(PickActivity.this, "Bild konnte nicht gelesen werden.", Toast.LENGTH_LONG).show();
                        finish();
                    }
                });
            }
        }).start();
    }

    /** Pictures older than a day were sent long ago. */
    private void cleanUp() {
        File[] old = ImageProvider.dir(this).listFiles();
        if (old != null)
            for (File f : old) if (System.currentTimeMillis() - f.lastModified() > 24 * 3600 * 1000L) f.delete();
    }
}
