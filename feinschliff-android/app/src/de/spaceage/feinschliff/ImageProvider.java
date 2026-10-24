package de.spaceage.feinschliff;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;

import java.io.File;
import java.io.FileNotFoundException;

/**
 * Hands the pictures picked for the keyboard (cache/images) to the app being typed in, and lets the
 * camera app write a new photo there. Not exported: other apps only get a single file, by URI grant.
 */
public class ImageProvider extends ContentProvider {
    static final String AUTHORITY = "de.spaceage.feinschliff.images";

    static File dir(Context c) {
        File d = new File(c.getCacheDir(), "images");
        d.mkdirs();
        return d;
    }

    static Uri uriFor(File f) { return Uri.parse("content://" + AUTHORITY + "/" + f.getName()); }

    static String mimeOf(String name) {
        String n = name.toLowerCase();
        if (n.endsWith(".png")) return "image/png";
        if (n.endsWith(".gif")) return "image/gif";
        if (n.endsWith(".webp")) return "image/webp";
        if (n.endsWith(".heic") || n.endsWith(".heif")) return "image/heic";
        return "image/jpeg";
    }

    private File file(Uri uri) throws FileNotFoundException {
        String n = uri.getLastPathSegment();
        if (n == null || !n.matches("[A-Za-z0-9._-]+") || n.startsWith(".")) throw new FileNotFoundException(String.valueOf(uri));
        return new File(dir(getContext()), n);
    }

    @Override public boolean onCreate() { return true; }

    @Override public String getType(Uri uri) { return mimeOf(String.valueOf(uri.getLastPathSegment())); }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        return ParcelFileDescriptor.open(file(uri), ParcelFileDescriptor.parseMode(mode));
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] args, String sort) {
        File f;
        try { f = file(uri); } catch (FileNotFoundException e) { return null; }
        String[] cols = projection != null ? projection : new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE};
        MatrixCursor c = new MatrixCursor(cols);
        Object[] row = new Object[cols.length];
        for (int i = 0; i < cols.length; i++)
            row[i] = OpenableColumns.DISPLAY_NAME.equals(cols[i]) ? f.getName() : OpenableColumns.SIZE.equals(cols[i]) ? f.length() : null;
        c.addRow(row);
        return c;
    }

    @Override public Uri insert(Uri uri, ContentValues values) { return null; }
    @Override public int delete(Uri uri, String selection, String[] args) { return 0; }
    @Override public int update(Uri uri, ContentValues values, String selection, String[] args) { return 0; }
}
