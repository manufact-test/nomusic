# Browser support candidate 0.4.76

Accepted 0.4.73 is preserved. This candidate adds automatic bounded diagnostics to ordinary support messages; playback algorithms are unchanged.

- Server candidate and rollout instructions: https://github.com/manufact-test/nomusic/blob/feature/server-general-support-attachments-20261111/docs/decisions/DESKTOP-SUPPORT-ATTACHMENTS-20261111.md
- Server review: https://github.com/manufact-test/nomusic/pull/40
- Verification: https://github.com/manufact-test/nomusic/actions/runs/42986349424 (365 tests, Chrome support form, persistence/export/privacy and W70 compatibility).
- ZIP SHA256: 16965deaee121dd9932fe3ba2df78fe8cc4ce9ebb0838324a08442123bc00b74 (2489958 bytes; identical local and CI builds).

**Server support is active (owner-approved 2026-11-11).** Release browser-support-076-8b66c9187413 passed live save/HTTPS retry/admin pages/protected download/privacy checks: https://github.com/manufact-test/nomusic/actions/runs/42989025119 . The owner can now install 0.4.76; its acceptance as the new reference remains pending. Shared Windows/Android ingress contract: https://github.com/manufact-test/nomusic/blob/feature/server-general-support-attachments-20261111/docs/support/SUPPORT-DIAGNOSTICS-CONTRACT-20261111.md . Do not replace the accepted reference archive or reintroduce experimental playback. The backend in this client snapshot is historical; use the separate server candidate above, never deploy the whole client branch's server directory.
