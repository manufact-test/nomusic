# Android CELIKOM documentation hygiene

**Purpose:** keep new chats small without losing technical evidence.

## Canonical files

- `NEXT-CHAT.md` is the only current-state handoff. Rewrite it when the state changes; never append a daily diary or a second full history.
- One short dated technical note may hold the proof for the active investigation.
- `NEXT-CHAT-START-MESSAGE-YYYYMMDD.md` mirrors the current handoff and is the copy/paste prompt. Keep it shorter than the handoff.
- External research belongs in a separate dated note only when it materially changes the search strategy.
- This policy file is the source of truth for documentation maintenance.

## Size and loading limits

- Aim for `NEXT-CHAT.md` ≤ 8 KB and ≤ 100 lines.
- Aim for a start message ≤ 3.5 KB.
- Keep an active technical note focused; split it only when independent topics genuinely need separate evidence.
- A new chat normally reads only `NEXT-CHAT.md` and the one active technical note. Research/closure notes are on-demand references.
- Never ask a new chat to read the whole `docs/android` folder or recursively ingest archives.

## Updating and archiving

1. Update the canonical handoff in place. Remove stale status and repeated history, but preserve current constraints, exact checkpoints, proven facts, unresolved facts and the next bounded task.
2. Before replacing a substantial historical handoff, copy the old file byte-for-byte into `docs/android/archive/` and link it from the current handoff or archive index.
3. Keep closed-route evidence available, clearly labelled CLOSED. Do not re-run it merely because a new chat starts.
4. Do not bulk-delete old evidence. Archive it or leave it as a linked reference; routine startup must not load it.
5. Maintain `archive/README.md` as the index of superseded handoffs and long historical notes. Keep legacy files in place if moving them would break relative links; mark them as non-startup references.
5. Keep one current start message. Update it in place instead of creating a new similarly named prompt every few hours.

## Logs and source files

- Never paste complete CI logs, raw audit JSON, DEX dumps or giant source files into chat.
- CI should emit a small allow-listed summary; raw reports stay temporary on the runner and are deleted. Do not upload them as artifacts.
- For large parser/test files, fetch exact line ranges around the target function only.
- Summaries should contain verdicts, counts and the minimum proof fields needed for the next decision. Never include private field names/values, user data, IDs, URLs, tokens or audio bytes.

## Checkpoint discipline

- Keep code checkpoints separate from documentation-only commits.
- After a substantial docs cleanup, create a named backup branch and verify its SHA against the working branch.
- Do not label a workflow change green until its own CI run completes successfully.
- A docs-only update must not silently change runtime code or hooks.

## Archive principle

Archives are evidence storage, not working context. Preserve them for auditability, but do not load them unless a specific unresolved question requires their contents.
