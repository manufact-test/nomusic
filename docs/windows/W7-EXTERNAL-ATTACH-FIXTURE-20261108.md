# W7 — isolated external attachment without ASAR patching

**2026-11-08. Scope:** `windows-companion/w7/**` and dedicated
Windows CI. This is a synthetic feasibility experiment, **not** a product
release, Yandex account integration or installed-client modification.

## Question addressed

W3 showed `getFileInfo` strings in the official packaged archive, but no
live instrumentation. W5 proved native single-decoder replacement on the
public Yandex web classes in **a separate Electron fixture**, not in the
owner's official Yandex application. W6 proved synthetic byte-verified
restoration; never touched the actual official EXE or ASAR.

W7 asks a narrower question: *can an external CELIKOM sidecar dynamically
reach a renderer and install the already-tested W4 native source adapter
without rewriting an Electron archive?* Answer in the experiment must
be determined by **an actual external Node process**, not an in-renderer
test that merely imports CELIKOM on its own.

## Experiment (allowlist only)

- A new disposable Electron 44.x fixture is created in Windows CI.
- It has no Yandex user session, credentials, original installed files,
  browser profile, backend access or real track audio.
- A temporary `--remote-debugging-port` is opened **only** by that
  test Electron process on 127.0.0.1. An independent Node sidecar discovers
  its DevTools page using `/json/list`, with strict exact URL, nonce,
  title, WebSocket path, host and port allowlists. The user app can never
  qualify for this gate.
- The sidecar permits only `Runtime.enable` and `Runtime.evaluate`;
  no requests for cookies, session storage, network responses, headers,
  credentials or user metadata. A nonce-bound, test-only expression imports
  `activation.mjs` into the fixture and activates W4.
- The renderer starts with pinned **actual public Yandex Music web**
  `getFileInfo`, batch resource and private native source classes but
  with no preinstalled CELIKOM integration. It is not the owner-installed
  `YandexMusic 5.126.1` runtime.
- After external activation, an independent Electron decoder plays
  generated synthetic MP3: test native pause, seek, Next, mixed batch,
  delayed stale response, original source reacquisition, Stop and
  single `HTMLAudioElement` ownership.
- Child process exit, assertions and CDP identity must all pass for green
  CI. Logs contain only test labels and counts, never DevTools URLs,
  passwords, captured pages, raw request headers or signed tokens.
- W4/W5/W6 and the existing W3 read-only safety checks remain in the
  same CI workflow.

## Why W7 is NOT a safe production attachment mechanism

Electron supports `--remote-debugging-port`, but Chrome DevTools Protocol
is a **powerful unrestricted debugger** for that renderer, not a limited
CELIKOM plugin API. Any local software able to reach an exposed port may
gain significant page access. Loopback does not make a user-account
debugger harmless. Do **not** enable or discover random debug ports on
an authenticated Yandex process and do not ship this sidecar as a client.

The official app was already running during W0–W3; there is no evidence its
current launch exposes a compatible debugging endpoint. Without an
authorized developer port or an official plugin interface, an external
process cannot simply call private Webpack resource methods from another
process. Injecting a preload, rewriting `app.asar`, rewriting a signed
EXE hash, launching with altered flags or patching DLLs is a **different**
and more hazardous class of intervention requiring explicit owner consent,
a signed/versioned compatibility strategy, rollback proof and legal
review. W6's synthetic backup is not sufficient for that.

Therefore a passing W7 proves **controlled debug-attach feasibility only**,
not a path acceptable for normal CELIKOM Windows installation.

Official Electron references:
- https://www.electronjs.org/docs/latest/api/command-line-switches
- https://www.electronjs.org/docs/latest/tutorial/context-isolation
- https://www.electronjs.org/docs/latest/tutorial/security

## Go/no-go for next stage

1. Prefer a documented, genuinely supported official Yandex renderer
   integration point if one can be independently verified.
2. If no supported API exists, assess narrowly scoped, explicit opt-in
   experimental patching **without disabling integrity checks or touching
   the original EXE**, and prove independent signed/hash-checked restoration
   on a full copy first.
3. Only after authorization run a minimal live compatibility observation
   on the owner's exact official build; avoid reading tokens and avoid
   using a second playing audio engine.
4. If the live attachment cannot be made safe and reversible, mark it
   NO-GO rather than claiming W5/W7 prove a finished product.

**No owner action or new test ZIP is needed for W7.**
