; CELIKOM native one-installer staging: CELIKOM files only, no bundled Yandex.

#define AppExecutable "CELIKOM.Companion.exe"

[Setup]
AppId={{D99FDB90-46BF-4EE5-989E-659A2B6450D6}
AppName=CELIKOM
AppVersion=0.24.2
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
OutputBaseFilename=CELIKOM-W29-NATIVE-SAFE-UNSIGNED
UninstallDisplayIcon={app}\{#AppExecutable}
CloseApplications=yes
RestartApplications=no
ChangesEnvironment=no

[Files]
Source: "..\publish\{#AppExecutable}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\w23\dist\host.cjs"; DestDir: "{app}\integration"; Flags: ignoreversion
Source: "..\..\w23\dist\renderer.js"; DestDir: "{app}\integration"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\CELIKOM"; Filename: "{app}\{#AppExecutable}"

[Run]
Filename: "{app}\{#AppExecutable}"; Description: "Открыть CELIKOM"; Flags: postinstall nowait skipifsilent

[Code]
function InitializeUninstall(): Boolean;
var
  ReturnCode: Integer;
begin
  Result := True;
  if FileExists(ExpandConstant('{app}\{#AppExecutable}')) then
  begin
    Result := Exec(ExpandConstant('{app}\{#AppExecutable}'),
      '--restore-native', '', SW_HIDE, ewWaitUntilTerminated, ReturnCode);
    if Result then Result := ReturnCode = 0;
    if not Result then
      MsgBox('Сначала закрой Яндекс.Музыку: CELIKOM не смог подтвердить восстановление оригинальных файлов.',
        mbError, MB_OK);
  end;
end;
