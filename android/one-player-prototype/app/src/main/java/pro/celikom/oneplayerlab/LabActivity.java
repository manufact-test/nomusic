package pro.celikom.oneplayerlab;

import android.app.Activity;
import android.content.Intent;
import android.media.MediaPlayer;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.*;
import pro.celikom.oneplayer.SourceGate;
import pro.celikom.oneplayer.SourceGate.*;

import java.io.IOException;

/**
 * Standalone local-file test harness. Not a Yandex client, patch or root module.
 * Single Android MediaPlayer is the ONLY audio engine in this process.
 */
public final class LabActivity extends Activity {
    private static final int ORIGINAL_REQUEST = 1001;
    private static final int REPLACEMENT_REQUEST = 1002;
    private Uri originalUri, replacementUri;
    private MediaPlayer player;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final String[] sourceNames = {"Original", "Replacement"};
    private EditText idInput, editionInput, candidateId, candidateEdition;
    private TextView status, position;
    private SeekBar seek;
    private Button playPause;
    private boolean tracking;
    private long originalDuration, replacementDuration;
    private String selectedSource = "None";

    @Override public void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(24, 16, 24, 16);
        ScrollView scroll = new ScrollView(this);
        scroll.addView(root);
        setContentView(scroll);

        label(root, "CELIKOM • ONE PLAYER LAB", 21);
        label(root, "Offline proof only. Not Yandex integration. Choose two audio files you own.", 13);
        button(root, "1. Select original file", () -> pick(ORIGINAL_REQUEST));
        button(root, "2. Select approved replacement file", () -> pick(REPLACEMENT_REQUEST));
        idInput = field(root, "Host verified catalog ID (lab simulation)", "42884423");
        editionInput = field(root, "Host edition ID (lab simulation)", "edition-A");
        candidateId = field(root, "Replacement catalog ID", "42884423");
        candidateEdition = field(root, "Replacement edition ID", "edition-A");
        button(root, "3. Prepare one source (original / replacement)", this::startSelected);
        playPause = button(root, "Play / Pause", this::togglePlay);
        button(root, "Seek −10 sec", () -> seekBy(-10000));
        button(root, "Seek +10 sec", () -> seekBy(10000));
        button(root, "Next = stop and prepare next original", this::nextStop);
        position = label(root, "00:00 / 00:00", 14);
        seek = new SeekBar(this);
        root.addView(seek);
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            public void onProgressChanged(SeekBar s, int p, boolean user) {
                if (user) position.setText(seconds(p) + " / " + seconds(s.getMax()));
            }
            public void onStartTrackingTouch(SeekBar s) { tracking = true; }
            public void onStopTrackingTouch(SeekBar s) {
                tracking = false;
                if (player != null) player.seekTo(s.getProgress());
            }
        });
        status = label(root, "Ready. No network, no other-app access.", 14);
        playPause.setEnabled(false);
        handler.post(updatePosition);
    }

    private void pick(int request) {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.setType("audio/*");
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(i,request);
    }

    @Override protected void onActivityResult(int req, int result, Intent data) {
        super.onActivityResult(req,result,data);
        if (result != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        try {
            getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (SecurityException ignored) {
            // Temporary grant remains valid for current session.
        }
        if (req == ORIGINAL_REQUEST) {
            originalUri = uri;
            originalDuration = readDuration(uri);
            show("Original selected: " + originalDuration + " ms");
        } else if (req == REPLACEMENT_REQUEST) {
            replacementUri = uri;
            replacementDuration = readDuration(uri);
            show("Replacement selected: " + replacementDuration + " ms");
        }
    }

    private long readDuration(Uri uri) {
        MediaPlayer probe = new MediaPlayer();
        try {
            probe.setDataSource(this,uri);
            probe.prepare();
            return probe.getDuration();
        } catch (Exception e) {
            return 0;
        } finally {
            probe.release();
        }
    }

    private void startSelected() {
        if (originalUri == null) { show("Select original file first"); return; }
        // This lab cannot attest IDs from Yandex. Lab input models the trusted host contract.
        Track original = new Track(value(idInput),value(editionInput),
            originalUri.toString(), originalDuration, Evidence.INTERNAL_CATALOG);
        Candidate replacement = replacementUri == null ? null : new Candidate(
            value(candidateId),value(candidateEdition),replacementUri.toString(),
            replacementDuration,true,true,true,true);
        Decision decision = SourceGate.select(original,replacement);
        Uri uri = Uri.parse(decision.uri);
        stopPlayer();
        player = new MediaPlayer();
        try {
            player.setDataSource(this,uri);
            player.setOnCompletionListener(mp -> {
                playPause.setText("Play / Pause");
                show("Ended: " + selectedSource);
            });
            player.prepare();
            player.start();
            selectedSource = decision.selection == Selection.REPLACEMENT ? sourceNames[1] : sourceNames[0];
            playPause.setEnabled(true);
            playPause.setText("Pause");
            seek.setMax(player.getDuration());
            show("Single-player source: " + selectedSource + " (" + decision.reason + ")");
        } catch (Exception e) {
            stopPlayer();
            if (decision.selection == Selection.REPLACEMENT) {
                // Once-only startup fallback; never switch live audio mid-track.
                prepareOriginalFallback("Replacement not playable");
            } else {
                show("Original not playable: " + e.getClass().getSimpleName());
            }
        }
    }

    private void prepareOriginalFallback(String reason) {
        if (originalUri == null) return;
        player = new MediaPlayer();
        try {
            player.setDataSource(this,originalUri);
            player.prepare();
            player.start();
            selectedSource = "Original";
            playPause.setEnabled(true);
            playPause.setText("Pause");
            seek.setMax(player.getDuration());
            show(reason + " -> original from start");
        } catch (Exception e) {
            stopPlayer();
            show("Original startup failed");
        }
    }

    private void togglePlay() {
        if (player == null) return;
        if (player.isPlaying()) {
            player.pause();
            playPause.setText("Play");
        } else {
            player.start();
            playPause.setText("Pause");
        }
    }

    private void seekBy(int delta) {
        if (player != null) player.seekTo(Math.max(0,
            Math.min(player.getDuration(),player.getCurrentPosition()+delta)));
    }

    private void nextStop() {
        // A real Next would receive the new item from the authorized host queue,
        // then decide BEFORE prepare. The lab has no Yandex queue.
        stopPlayer();
        show("Next boundary: previous decoder released. Choose next original file.");
        pick(ORIGINAL_REQUEST);
    }

    private void stopPlayer() {
        if (player != null) {
            try { player.stop(); } catch (IllegalStateException ignored) {}
            player.release();
            player = null;
        }
        playPause.setEnabled(false);
        playPause.setText("Play / Pause");
    }

    private final Runnable updatePosition = new Runnable() {
        @Override public void run() {
            if (player != null && !tracking) {
                try {
                    int ms = player.getCurrentPosition();
                    seek.setProgress(ms);
                    position.setText(seconds(ms) + " / " + seconds(player.getDuration()));
                } catch (IllegalStateException ignored) {}
            }
            handler.postDelayed(this,250);
        }
    };

    private String seconds(long ms) {
        long s = ms / 1000;
        return String.format(java.util.Locale.ROOT,"%02d:%02d",s/60,s%60);
    }
    private String value(EditText e) { return e.getText().toString().trim(); }
    private TextView label(LinearLayout root, String text, int sp) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextSize(sp);
        t.setPadding(0,8,0,8);
        root.addView(t);
        return t;
    }
    private EditText field(LinearLayout root,String hint,String value) {
        EditText e = new EditText(this);
        e.setSingleLine(true);
        e.setHint(hint);
        e.setText(value);
        root.addView(e);
        return e;
    }
    private Button button(LinearLayout root,String title,Runnable action) {
        Button b = new Button(this);
        b.setText(title);
        root.addView(b);
        b.setOnClickListener(v -> action.run());
        return b;
    }
    private void show(String s) { if (status != null) status.setText(s); }
    @Override protected void onDestroy() {
        handler.removeCallbacks(updatePosition);
        stopPlayer();
        super.onDestroy();
    }
}
