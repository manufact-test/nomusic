CELIKOM Companion for Windows — W15 PREVIEW / ISOLATED TEST ONLY
===============================================================

What is included:
- CELIKOM.Companion.exe : native .NET 10 Windows app (own CELIKOM login, Start/Stop,
  one-time pairing code, local bridge only). It does NOT play audio.
- addon/<GUID>/script.js and metadata: PulseSync SDK add-on code.
- SHA-256 digests for both artifacts.

What is NOT included:
- Yandex Music, PulseSync Client/mod or installers for either;
- Any patcher, debugger, security bypass, API credentials or music files.

Your existing Yandex Music installation is UNTOUCHED by this package.
Do NOT install mods on your everyday signed-in Yandex installation for this test.
For first real-client testing use the isolated/snapshotted Windows VM in the
W14 safety plan, with Windows Defender and SmartScreen enabled. PulseSync
itself modifies signed vendor files and may trigger Windows protection.

The product needs a valid HTTPS API address from your existing CELIKOM backend.
The add-on can pair only after the Companion app is running. It has no
Yandex credentials and uses only 127.0.0.1:21471.

W15 CI proves compilation and offline safety contracts, not audible native
source replacement. Never treat this build as approved commercial distribution.
PulseSync Client commercial redistribution is subject to separate permission.

Full instructions and known blockers are in:
docs/windows/W14-FIRST-REAL-CLIENT-TEST-PLAN-20261109.md
windows-companion/w15/README.md
