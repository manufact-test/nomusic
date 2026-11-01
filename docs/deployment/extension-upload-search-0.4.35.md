# CELIKOM 0.4.35: upload checks and moderation order

Owner report (2026-10-13): after uploading a song and choosing another through Yandex search, opening upload intermittently shows a generic connection error until page reload. The screenshot does not identify the failed endpoint or prove one network cause.

Changes:
- Moderation sorts the entire uploads query before pagination: pending, other decisions, approved; newest ID first within each group. Status filters remain available.
- Upload presence GET retries once on transport/timeout, server 5xx or rejected access token (obtaining fresh contribution access). MP3 POST is never automatically replayed.
- A failed opening can be retried with one click; it does not just close the error panel. Previous form data is retired if the initial controller read fails.
- Opening compares the response with the pinned track. Submission checks track identity again after presence and credential requests, before sending audio.
- Active replacement says «Играет версия CELIKOM», paused replacement says «Версия CELIKOM на паузе». Return to original restores the availability label.

Validation: 188 extension tests pass, including temporary 503 recovery, failed-opening retry, track switch during lookup and active/pause/original labels. Manifest and client security checks pass. MySQL-backed moderation regression and deployment are checked by the Hostinger workflow before activation.

Owner acceptance remaining: update the extension, reload the existing Yandex page once, upload a song then select another through search and open/upload without subsequent reload; verify active and paused labels; verify an older pending card appears above a newer approved card in the unfiltered admin list.

Client ZIP: CELIKOM-0.4.35-full.zip. SHA256 eba80dd4626a68319455a835f0b9830dd481d2b28f484ad9c3f231a10b5a4b59. Configured API: https://darkred-camel-588676.hostingersite.com.
