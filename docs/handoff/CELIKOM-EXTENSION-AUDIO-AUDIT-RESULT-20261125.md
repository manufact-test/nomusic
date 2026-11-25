# Floki audio body audit result —25 November2026

Owner supplied `Вставленный текст(20261125-200132).txt` (Library libfile_ffab8c39fe9081919d68fef399acf9b6) from the exact pinned read-only script a6d036cfad5a06c3db448764ac8fbd163d036147 / blob9976a77259f7d1b40af5e6b86ff4384c25768eb8.

## Verified live results

All16 signed HTTP206 requests completed with exact byte count,Content-Range,ETag and matching SHA256 against the same local storage range. Track144530503 Ау is4,345,176bytes/180,872ms. No account/session/trial/config/source writes were performed.

| Route from VPS | Requested bytes | Samples | Total min–max | Median |
| --- | --- | --- | --- | --- |
| Loopback HTTPS |65536|4|92.63–96.93ms|94.98ms|
| Loopback HTTPS |524288|4|98.85–119.66ms|103.215ms|
| Public DNS HTTPS |65536|4|109.72–210.10ms|126.99ms|
| Public DNS HTTPS |524288|4|111.02–162.88ms|120.46ms|

Both offsets0/65536 and both rounds succeeded. Body64KiB progress milestones advance continuously. `first_body_ms` uses a PHP clock started before curl setup; `total_ms` is libcurl's internal duration, so a small first-body>total difference is not a negative network duration.

Deployed AudioController/Response/AudioAccessService/ByteRange blobs match the0.4.73 baseline. Modes0640 are currently functional; do not change permissions speculatively. Nginx syntax passes. Load0.04/0.21/0.82;MemAvailable2,922,036KiB of4,009,096KiB;diskavailable40,736,964,608bytes. No overload or incomplete response was observed in this measurement. FPM output_buffering4096,zlibOff,implicit_flushOff,max_execution_time30 are observations, not evidence that they need changing.

## Limits of conclusion

BOTH loopback and public DNS requests originated on the SAME VPS. Public DNS is not an independent external client. This verifies the deployed storage→PHP→Nginx path at the measurement time, not the owner's ISP/VPN/Brave path, HTTP protocol or browser content-encoding behavior. It does not prove Floki networking is universally healthy or that prior intermittent server load never occurred. Do not change Nginx/FPM or blame VPN solely from these results.

## Next minimal control

Use the already accepted exact0.4.73 immutable owner ZIP with the new API, without rebuilding/relabeling it. Local retained ZIP rechecked:2,489,436bytes,SHA256968e34ef72927ce5be5007d1ed210a9b6910b45d4fa423b67fdc3db16a75becb;manifest0.4.73,api/config.json=https://api.celikom.com,host permissions exactly API+music.yandex.ru,ZIP integrity PASS. Existing historical owner URL is https://celikom.com/downloads/extension/celikom-extension-0.4.73.zip (private Basic auth retained); this turn did not independently fetch it over authenticated HTTPS. Exact-byte fallback copy saved privately as libfile_ebdf477e7478819195ff918f0064ffea,filename celikom-extension-0.4.73(1).zip. Download suffix is a duplicate filename, not a code revision.

Owner replaces same unpacked folder,reloads extension AND Yandex tab,confirms reported version0.4.73,then tests the same Au track ordinary playback/seek39s and a couple of track switches on the SAME network/VPN state as failure. Do not install a second simultaneous CELIKOM instance or alter network state during this control. Request one diagnostic after the control. If exact baseline also starves, prioritize actual client-path measurement; if baseline works while83 fails under matched conditions, compare added guards/revalidation before further buffering redesign. A baseline control can still contain the reproduced old unbuffered-seek gap; do not call it fixed based on historical acceptance.

0.4.84 stays HELD and owner promotions remain empty. No new version/publication/production setting change in this result analysis; Android/Windows unchanged. Do not give84 as accepted or update website latest. The current main source contains the held84 candidate; control ZIP is the preserved73 artifact, not a rollback of shared main.
