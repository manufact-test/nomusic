; CELIKOM W20 INTERNAL INSTALLER - NOT A CONSUMER AUDIO RELEASE
; Installs ONLY the CELIKOM-owned Companion. No Yandex/PulseSync binaries, mods,
; profile access, Windows security changes, drivers or admin elevation.

#define AppExecutable "CELIKOM.Companion.exe"

[Setup]
AppId={{D99FDB90-46BF-4EE5-989E-659A2B6450D6}
AppName=CELIKOM (internal staging)
AppVersion=0.20.0
AppPublisher=CELIKOM
DefaultDirName={localappdata}\Programs\CELIKOM
DefaultGroupName=CELIKOM
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
DisableDirPage=yes
OutputDir=..\output
OutputBaseFilename=CELIKOM-W20-INTERNAL-UNSIGNED
UninstallDisplayIcon={app}\{#AppExecutable}
CloseApplications=yes
RestartApplications=no
ChangesEnvironment=no

[Files]
Source: "..\publish\{#AppExecutable}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\CELIKOM (internal staging)"; Filename: "{app}\{#AppExecutable}"

[Run]
Filename: "{app}\{#AppExecutable}"; Description: "Открыть CELIKOM (внутренний тест)"; Flags: postinstall nowait skipifsilent
