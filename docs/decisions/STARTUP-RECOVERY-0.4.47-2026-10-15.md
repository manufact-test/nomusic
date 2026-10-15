# CELIKOM 0.4.47 — explicit retry and startup diagnosis

Owner reports .46 seemingly turning itself on/off. Evidence from the two attached diagnostics:

- Enabled remains true; MAIN bridge is healthy. First report has replacement-load-timeout for 48591518 (Моя игра), replacement decoder readyState 0 and auth transport failures without HTTP status. This confirms interrupted loading, not the cause of the underlying connection loss.
- Later reports READY with repeated PREPARING at approximately 15 s intervals but no RESTORING. This is the existing negative resolve TTL, not repeated disabling.
- Restricted live audit 38746323131 verified release .46-f2d1cc31f598a983c46660688b453392faf0fc8d. 48591518 is approved/active MP3 replacement 17, 13398804 bytes present, ID3 15751 bytes. IDs 34139530 (Романс), 39013770 (Муза), 48592008 and 105553785 have no uploaded mapping. Health/config returned 200. Do not invent or reactivate mappings for them. Papirosy 1944599 is now an owner-approved M4A; preserve it.

The old explicit configure/start path cleared retry flags but retained an in-flight operation. A stalled resolve/load therefore remained authoritative after pressing Start. UI disabled Start throughout PREPARING, so a delayed automatic recovery appeared to be the only available action.

Changes:
- Explicit retry synchronously disposes the current operation and fences late resolution/decoder readiness; no late playback resurrection. Worker also resets the playback API read transport, in addition to auth transport. No write retry.
- Overall worker resolve message wait is bounded at 30 s. Every MP3 range has a 15 s deadline, including body/append; stalled ongoing downloads fail open with existing bounded recovery. Native container network failures receive typed transient errors instead of terminal raw fetch messages. No weakening of authorization, signed tokens, MIME/range validation or moderation.
- READY explicitly says “Включён · играет оригинал”. PREPARING distinguishes resolution/loading; after 10 s “Повторить” becomes available. Suspended/recovering access also permits manual retry. Preparation stays gray consistently with the existing toolbar.
- Diagnostics expose stage/elapsed time/stream progress, network status and offset. API request history includes resolve status/timing without query strings, track history, signed URLs or tokens. Auth transport failures preserve network error meaning across the API broker. Negative resolution is logged as NO_REPLACEMENT.

Actual external cause of the intermittent connection loss is still unknown; do not attribute it to the owner's VPN/provider or claim it fixed. Added user control and bounded recovery fix verified software gaps. No backend deploy or library mutation is necessary; backend remains .46. Preserve MP3/M4A behavior and .46 assigned/current resource identity guard. Wrong-song fragment remains awaiting owner acceptance. PR #6 and issue #7 stay open.
