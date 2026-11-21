# CELIKOM 0.4.37: natural completion and stale ended events

Owner report: in 0.4.36, after track 48592437 completes, new exact track 48591588 is READY but master-ended remains, active=null and recovering=false. Recent auth/config requests all succeeded. The prior UI/upload release did not modify playback control other than its build version; nevertheless the current completion path is faulty and required a direct regression fix.

Reproduced before fixing: a late ENDED snapshot with ended=false blocks the newly selected track; natural ENDED marks normal completion as an error. All three added adapter/engine tests failed against the previous code.

Fix: adapter ignores an ended event when the selected media is no longer ended. MAIN-world bridge does not release on an unconfirmed ended event. Controller releases a genuine completed master without a permanent track block; a late ended snapshot is reconciled as current state. Error, stream-rebinding, manual bypass and authorization safeguards remain covered by existing tests.

Validation: 192 extension tests pass, including six consecutive track completions and a packaged MAIN+ISOLATED integration test for late ended, real completion, original restoration and automatic rearming without Start/reload. Configured API, manifest and client security checks pass. Physical playlist acceptance remains with owner; do not claim the real Yandex playlist is already verified.
