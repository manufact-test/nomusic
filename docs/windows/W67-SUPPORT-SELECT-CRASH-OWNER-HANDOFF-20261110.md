# W67 — CELIKOM Windows 0.24.14 support dropdown crash: urgent owner handoff (2026-11-10)

## Owner confirmation and severity

**Owner personally installed W66 / Windows 0.24.14** and reported the newest issue after several successful UI/audio stages. This is a **blocking defect (P0 for the Windows UX)**, not cosmetics. The application **closes completely** while working with the drop-down **“Вид обращения”** inside the expanded **“Связь с поддержкой”** card. The user tried other buttons and reported normal behavior there; the closure is associated specifically with entering/choosing between the two support types. Do not treat this as merely the support panel collapsing. **Exact process exception/exit cause is NOT confirmed** — instrument and reproduce before asserting cause.

The user supplied two screenshots in the conversation dated **2026-11-10**. They show the real compact Windows support dropdown and owner-highlighted issues. The screenshots are in the owner chat, not committed as assets.

### Three new defects to fix together

1. **Drop-down spills outside compact window.** When opened, the list extends significantly to the right, beyond the actual CELIKOM popup. Both choices should fit **inside the visible compact app/window bounds**, even when the form is against the screen edge, on varied DPI. Preserve dark palette and full readable options if possible with a bounded popup or wrapped text.
2. **Menu item text/selection alignment.** The item label/highlight looks vertically or horizontally off-center compared to the menu row, especially while hovering or selecting **“Проблема с текущей песней”**. Center text vertically and use consistent horizontal padding; avoid default/native unexplained indent, clipped text and misaligned highlight.
3. **CRITICAL: application closes entirely when interacting with support type selector.** Repro: launch existing 0.24.14; Account signed in; expand **Связь с поддержкой** → click **Вид обращения** → move/click between **Обычное обращение · ответ по почте** and **Проблема с текущей песней**. The owner reports that the whole Windows app exits when using this particular dropdown, while other UI remains functional. Capture actual unhandled WinForms exception / event sequence / Windows crash detail (log minimally without user data). Fix the root cause; test repeated changes and open/close cycles with mouse and keyboard. **Do not merely catch and hide fatal failures.**

### Read-only source inspection: exact likely code area (not a proven crash diagnosis)

- `windows-companion/w15/Celikom.Companion/PopupOptionSelect.cs`: custom owner-drawn `PopupOptionSelect : Control`. `ShowOptions()` creates a `ContextMenuStrip { AutoSize = false, Width = Math.Max(Width, DropDownWidth) }`, `ToolStripMenuItem` for each choice, `item.Click += (_, _) => { SelectedIndex = index; menu.Close(); }`, `menu.Closed += (_, _) => menu.Dispose();`. `SelectedIndex` synchronously fires `SelectedIndexChanged`.
- `windows-companion/w15/Celikom.Companion/CompactPopup.cs`: `_compactSupportKind.DropDownWidth = 300`, which **directly explains the excessive width** when the actual selector is narrower. `_compactSupportKind.SelectedIndexChanged += (_, _) => LayoutCompact();`; the layout may run **while `ContextMenuStrip` is still open**, changing support panel contents and heights. This interaction/reentrancy and disposal sequence is a **candidate** for the crash; verify rather than assume. The category selector is also `PopupOptionSelect`; inspect both.
- `windows-companion/w15/Celikom.Companion/CompactPopupActions.cs`: `CompactSendSupportAsync` uses the selected support type to send the correct server request. Owner previously confirmed that support form **does send and messages reach admin**. Do not rewrite or break API submission.
- `windows-companion/w59/Celikom.VisualPreview/Program.cs` currently sets `SelectedIndex` programmatically and verifies screenshot/geometry, but **does not test actual clicking the dropdown item / `ContextMenuStrip` lifecycle**. This is a test coverage gap. A successful screenshot suite did not validate owner behavior.

Suggested robust direction: bound popup width to available window/card width (not a hardcoded 300); avoid reentrant layout/disposal during `ToolStripMenuItem.Click` or `Closed`; consider deferring UI re-layout after menu closure or use stable custom drawn menu with predictable event ordering. Ensure selected text and active hover row align; preserve keyboard arrows, Enter, mouse, dark style and real support category selection.

**Repro/acceptance checks:** choose option A→B→A repeatedly (e.g. 20 cycles); click outside/close/reopen; keyboard Up/Down/Enter; DPI 100% and 125% if available; no app exit, no unhandled exception, popup contained within app, text centered. Switch to song issue and confirm category field correctly appears/disappears, wheel scroll remains functional, support can still be submitted and routed appropriately without duplicate tickets. Use a test API/stub for submissions, not unsolicited real customer messages.

## Source, exact safe rollback, constraints

- Repository: `manufact-test/nomusic`.
- Current working branch: `experiment/windows-stop-lifecycle-20261110`.
- Read-only inspected branch HEAD before this document: `326f57e4e1921bc413bade4594517d9f0d9c2007`; this handoff changes **documentation ONLY**, not application sources or binary.
- Current installed owner-candidate: Windows **0.24.14 / W66**.
- **W66 exact built source immutable backup:** `backup/windows-w66-02414-built-ci-passed-await-owner-20261110` @ `6b4a8088b299f802366bc85e3ff28515930336e4`.
- Previous W65 test version 0.24.13: `backup/windows-w65-02413-built-ci-passed-await-owner-20261110` @ `5ce1b6ebdecf9a49259d29241e5aa29619d2f429`; last safe alternative if selector crash makes W66 unusable. Owner-accepted sound baseline `backup/windows-w61-0249-audio-owner-approved-before-ui-parity-20261110` @ `44e69d78b459ed512862819280ebdb8b3dbc7e7d` remains untouched.
- W66 build CI: https://github.com/manufact-test/nomusic/actions/runs/42846306058 ; W66 synthetic same-user **0.24.13→0.24.14** upgrade: https://github.com/manufact-test/nomusic/actions/runs/42846415169 ; W66 UI screenshots: https://github.com/manufact-test/nomusic/actions/runs/42845448149.
- W66 unsigned owner EXE: `CELIKOM-W66-COMPACT-UX-BRAND-UNSIGNED.exe`, SHA256 `2028f53113eef88cfc65b4181336fc9db723a7360a051a551b280863668493f9`, GitHub artifact `13777993165`, Library `/CELIKOM/Windows/`, file id `file_00000000a96c8243811ad4bc82387b4b`. These are historical verified files, NOT a new W67 build.

**Do not:** create a new app, modify accepted 0.24.14 backup, Android Test.50, production, the original Yandex app, private server secrets, audio start/stop/seek/pause/MyWave source reload or unrelated extension logic. Maintain same installer AppId and existing DPAPI account session. Support diagnostics only to the two admin identities.

## Deliverable for next chat (W67 / likely Windows 0.24.15)

Fix all **three** selector issues in one substantive block, add a **real interaction** test that clicks the `ToolStripMenuItem` and exercises the entire lifecycle (not only setting index), then verify real Windows render and no process termination. Build a private candidate with GitHub Actions, verify installer SHA, independent upgrade `0.24.14 → 0.24.15` preserving session/one app/Yandex originals, upload exact EXE to **ChatGPT Library → CELIKOM → Windows**, and give the owner a **Library file card**, not an unverified sandbox link. Keep W66 rollback. The real owner must test the crash fix before it is called accepted.

**Communication preference:** do the block independently; send one succinct result when the installable build is ready, no small recurring progress reports. If build or CI fails, state that plainly, do not ship it.
