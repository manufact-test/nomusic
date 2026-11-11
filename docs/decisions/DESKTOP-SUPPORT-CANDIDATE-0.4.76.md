# Browser support candidate 0.4.76

Accepted 0.4.73 is preserved. This candidate adds automatic bounded diagnostics to ordinary support messages; playback algorithms are unchanged.

- Server candidate and rollout instructions: https://github.com/manufact-test/nomusic/blob/feature/server-general-support-attachments-20261111/docs/decisions/DESKTOP-SUPPORT-ATTACHMENTS-20261111.md
- Server review: https://github.com/manufact-test/nomusic/pull/40
- Verification: https://github.com/manufact-test/nomusic/actions/runs/42986349424 (365 tests, Chrome support form, persistence/export/privacy and W70 compatibility).
- ZIP SHA256: 16965deaee121dd9932fe3ba2df78fe8cc4ce9ebb0838324a08442123bc00b74 (2489958 bytes; identical local and CI builds).

**Not active on the shared server yet.** Ordinary attachments require the server candidate first. Do not replace the accepted reference archive or reintroduce experimental playback. The backend in this client snapshot is historical; use the separate server candidate above, never deploy the whole client branch's server directory.
