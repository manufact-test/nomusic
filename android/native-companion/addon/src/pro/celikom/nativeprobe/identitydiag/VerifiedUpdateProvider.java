package pro.celikom.nativeprobe.identitydiag;

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
 * Read-only one-file handoff to Android's normal APK viewer/installer.
 * The downloaded APK is verified by UpdateCenter before becoming visible here.
 * This provider is not exported; only a one-time URI grant accompanies the
 * user-initiated ACTION_VIEW intent.
 */
public final class VerifiedUpdateProvider extends ContentProvider {
    private static final String FILE_NAME = "celikom-verified-update.apk";
    private static final String URI_PATH = "/release.apk";
    static final String APK_MIME = "application/vnd.android.package-archive";

    static File verifiedFile(Context context) {
        return new File(context.getFilesDir(), FILE_NAME);
    }

    static Uri contentUri(Context context) {
        return new Uri.Builder()
            .scheme("content")
            .authority(context.getPackageName() + ".verified-update")
            .path(URI_PATH)
            .build();
    }

    private File requestedFile(Uri uri) throws FileNotFoundException {
        Context context = getContext();
        if (context == null || uri == null
                || !"content".equals(uri.getScheme())
                || !(context.getPackageName() + ".verified-update").equals(uri.getAuthority())
                || !URI_PATH.equals(uri.getPath())) {
            throw new FileNotFoundException("Unknown update URI");
        }
        File file = verifiedFile(context);
        if (!file.isFile()) throw new FileNotFoundException("No verified update");
        return file;
    }

    @Override public boolean onCreate() {
        return true;
    }

    @Override public String getType(Uri uri) {
        try { requestedFile(uri); }
        catch (FileNotFoundException invalid) { throw new IllegalArgumentException(invalid); }
        return APK_MIME;
    }

    @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        if (!"r".equals(mode)) throw new FileNotFoundException("Read-only APK");
        return ParcelFileDescriptor.open(requestedFile(uri), ParcelFileDescriptor.MODE_READ_ONLY);
    }

    @Override public Cursor query(Uri uri, String[] projection, String selection,
                                   String[] selectionArgs, String sortOrder) {
        File file;
        try { file = requestedFile(uri); }
        catch (FileNotFoundException invalid) { throw new IllegalArgumentException(invalid); }
        String[] columns = projection == null
            ? new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE}
            : projection;
        MatrixCursor result = new MatrixCursor(columns, 1);
        Object[] row = new Object[columns.length];
        for (int i = 0; i < columns.length; i++) {
            if (OpenableColumns.DISPLAY_NAME.equals(columns[i])) row[i] = "CELIKOM.apk";
            else if (OpenableColumns.SIZE.equals(columns[i])) row[i] = file.length();
        }
        result.addRow(row);
        return result;
    }

    @Override public Uri insert(Uri uri, ContentValues values) {
        throw new UnsupportedOperationException("Read-only APK");
    }

    @Override public int update(Uri uri, ContentValues values, String selection,
                                String[] selectionArgs) {
        throw new UnsupportedOperationException("Read-only APK");
    }

    @Override public int delete(Uri uri, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("Read-only APK");
    }
}
