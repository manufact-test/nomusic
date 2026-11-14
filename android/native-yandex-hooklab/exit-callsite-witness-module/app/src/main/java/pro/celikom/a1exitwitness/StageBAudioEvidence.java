package pro.celikom.a1exitwitness;

import java.util.concurrent.atomic.AtomicLong;

/**
 * Session-local privacy-safe Stage B evidence from the *actual scoped native
 * module*, not the separate B42 JS / Java models. It records only finite,
 * categorised framework source-reader observations; never bytes, offsets,
 * source addresses, account values, identifiers, signed URLs or file paths.
 *
 * A reader invocation, even one linked by Java identity to MediaExtractor,
 * is NOT proof of the audible current track or an applied CELIKOM replacement.
 * Export runs only when the owner explicitly saves diagnostics.
 */
final class StageBAudioEvidence {
    private final AtomicLong reader0 = new AtomicLong();
    private final AtomicLong reader1 = new AtomicLong();
    private final AtomicLong extractor0 = new AtomicLong();
    private final AtomicLong extractor1 = new AtomicLong();
    private final AtomicLong extractorOther = new AtomicLong();
    private final AtomicLong sameObjectReads = new AtomicLong();
    private final AtomicLong positiveReads = new AtomicLong();
    private final AtomicLong endOfSourceReads = new AtomicLong();
    private final AtomicLong failedReads = new AtomicLong();

    void onReader(int candidate, boolean wasPassedToExtractor) {
        if (candidate == 0) reader0.incrementAndGet();
        else if (candidate == 1) reader1.incrementAndGet();
        if (wasPassedToExtractor) sameObjectReads.incrementAndGet();
    }

    void onExtractorSource(int candidate) {
        if (candidate == 0) extractor0.incrementAndGet();
        else if (candidate == 1) extractor1.incrementAndGet();
        else extractorOther.incrementAndGet();
    }

    void onReadReturn(int count) {
        if (count > 0) positiveReads.incrementAndGet();
        else if (count < 0 && count != Integer.MIN_VALUE)
            endOfSourceReads.incrementAndGet();
    }

    void onReadException() {
        failedReads.incrementAndGet();
    }

    private static String band(long count) {
        if (count <= 0) return "NONE";
        if (count == 1) return "ONE";
        if (count <= 8) return "FEW";
        return "MANY";
    }

    private static String event(String category, AtomicLong counter) {
        return "event=AUDIO_STAGE_B_SUMMARY;origin=" + category
            + ";error=" + band(counter.get()) + ";thread=OTHER";
    }

    String[] exportLines() {
        return new String[] {
            event("READER_0", reader0),
            event("READER_1", reader1),
            event("EXTRACTOR_0", extractor0),
            event("EXTRACTOR_1", extractor1),
            event("EXTRACTOR_OTHER", extractorOther),
            event("SAME_SOURCE_OBJECT", sameObjectReads),
            event("POSITIVE_READS", positiveReads),
            event("SOURCE_END", endOfSourceReads),
            event("READ_EXCEPTIONS", failedReads),
            "event=AUDIO_STAGE_B_STATUS;origin=CELIKOM_REPLACEMENT;error=NOT_CONNECTED;thread=OTHER"
        };
    }
}
