; CELIKOM native one-installer staging: CELIKOM files only, no bundled Yandex.

#define AppExecutable "CELIKOM.Companion.exe"

[Setup]
AppId={{D99FDB90-46BF-4EE5-989E-659A2B6450D6}
AppName=CELIKOM
AppVersion=0.24.22
VersionInfoVersion=0.24.22.0
VersionInfoCompany=CELIKOM
VersionInfoProductName=CELIKOM
VersionInfoDescription=CELIKOM Windows Setup
AppPublisher=CELIKOM
DefaultDirName={localappdata}\Programs\CELIKOM
DefaultGroupName=CELIKOM
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
MinVersion=10.0
WizardStyle=modern
SetupIconFile=..\\assets\\CELIKOM.ico
Compression=lzma2
SolidCompression=yes
DisableDirPage=yes
OutputDir=..\output
OutputBaseFilename=CELIKOM-W75-PERSISTENT-DIAGNOSTICS-UNSIGNED
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
Filename: "{app}\{#AppExecutable}"; Parameters: "--complete-update"; Flags: nowait; Check: IsAppUpdate
Filename: "{app}\{#AppExecutable}"; Description: "Открыть CELIKOM"; Flags: postinstall nowait skipifsilent; Check: IsNormalInstall

[Code]
var
  RemoveSavedLoginOnUninstall: Boolean;

function IsAppUpdate(): Boolean;
begin
  Result := ExpandConstant('{param:CELIKOMAPPUPDATE|0}') = '1';
end;

function IsNormalInstall(): Boolean;
begin
  Result := not IsAppUpdate();
end;

function IsUninstallSilent(): Boolean;
var
  Tail: String;
begin
  Tail := UpperCase(GetCmdTail());
  Result := (Pos('/VERYSILENT', Tail) > 0) or (Pos('/SILENT', Tail) > 0);
end;

// Uninstall has no wizard pages. A separate modal form presents an actual
// unchecked checkbox BEFORE any restore/cleanup. Cancel aborts with no
// application or local-account changes. This is NOT invoked by setup/update.
function AskRemoveSavedLogin(): Boolean;
var
  Form: TSetupForm;
  Intro, Explanation: TLabel;
  RemoveCheck: TNewCheckBox;
  ContinueButton, CancelButton: TNewButton;
begin
  // Inno Setup 6.6+: CreateCustomForm requires explicit unscaled size,
  // KeepSizeX and KeepSizeY at construction (properties are read-only).
  Form := CreateCustomForm(480, 194, True, True);
  try
    Form.Caption := 'CELIKOM — удаление';

    Intro := TLabel.Create(Form);
    Intro.Parent := Form;
    Intro.Left := ScaleX(18);
    Intro.Top := ScaleY(15);
    Intro.Width := Form.ClientWidth - ScaleX(36);
    Intro.Height := ScaleY(45);
    Intro.AutoSize := False;
    Intro.WordWrap := True;
    Intro.Caption := 'Удалить CELIKOM с компьютера?' #13#10 +
      'По умолчанию сохранённый вход в аккаунт останется.';

    RemoveCheck := TNewCheckBox.Create(Form);
    RemoveCheck.Parent := Form;
    RemoveCheck.Left := ScaleX(18);
    RemoveCheck.Top := ScaleY(69);
    RemoveCheck.Width := Form.ClientWidth - ScaleX(36);
    RemoveCheck.Height := ScaleY(26);
    RemoveCheck.Caption := 'Также удалить сохранённые данные входа';
    RemoveCheck.Checked := False; // Uninstall/reinstall preserves sign-in by default.

    Explanation := TLabel.Create(Form);
    Explanation.Parent := Form;
    Explanation.Left := ScaleX(38);
    Explanation.Top := ScaleY(104);
    Explanation.Width := Form.ClientWidth - ScaleX(56);
    Explanation.Height := ScaleY(40);
    Explanation.AutoSize := False;
    Explanation.WordWrap := True;
    Explanation.Caption := 'При следующей установке потребуется войти заново. ' +
      'Пробный период и подписка на сервере не сбросятся.';

    ContinueButton := TNewButton.Create(Form);
    ContinueButton.Parent := Form;
    ContinueButton.Left := Form.ClientWidth - ScaleX(308);
    ContinueButton.Top := Form.ClientHeight - ScaleY(34);
    ContinueButton.Width := ScaleX(180);
    ContinueButton.Height := ScaleY(26);
    ContinueButton.Caption := 'Продолжить удаление';
    ContinueButton.ModalResult := mrOk;
    ContinueButton.Default := True;

    CancelButton := TNewButton.Create(Form);
    CancelButton.Parent := Form;
    CancelButton.Left := Form.ClientWidth - ScaleX(118);
    CancelButton.Top := ContinueButton.Top;
    CancelButton.Width := ScaleX(100);
    CancelButton.Height := ScaleY(26);
    CancelButton.Caption := 'Отмена';
    CancelButton.ModalResult := mrCancel;
    CancelButton.Cancel := True;

    Form.ActiveControl := RemoveCheck;
    Result := Form.ShowModal() = mrOk;
    if Result then RemoveSavedLoginOnUninstall := RemoveCheck.Checked;
  finally
    Form.Free();
  end;
end;

function InitializeUninstall(): Boolean;
var
  ReturnCode: Integer;
begin
  RemoveSavedLoginOnUninstall := False;
  // Automated maintenance never deletes login accidentally. The explicit
  // command-line opt-in exists for noninteractive CI/managed cleanup only.
  if IsUninstallSilent() then
    RemoveSavedLoginOnUninstall :=
      Pos('/CELIKOMREMOVELOGIN=1', UpperCase(GetCmdTail())) > 0
  else if not AskRemoveSavedLogin() then
  begin
    Result := False;
    Exit;
  end;

  Result := True;
  // Native Yandex restoration is mandatory BEFORE the app can be removed.
  // If it fails, neither uninstall nor opted-in session deletion proceeds.
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

// Only remove the exact DPAPI session file of this Windows user. Do not
// recursively delete CELIKOM app data: it may contain diagnostics/files.
// Never touch other users, server trials/subscriptions or Yandex files.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  SessionPath: String;
begin
  if (CurUninstallStep = usPostUninstall) and RemoveSavedLoginOnUninstall then
  begin
    SessionPath := ExpandConstant('{localappdata}\CELIKOM\Windows\session.dpapi');
    if FileExists(SessionPath) then
    begin
      if DeleteFile(SessionPath) then
        Log('CELIKOM opt-in saved-login removal succeeded')
      else
      begin
        Log('CELIKOM opted-in saved-login removal failed');
        if not IsUninstallSilent() then
          MsgBox('CELIKOM удалён, но сохранить данные входа не удалось удалить. ' +
            'Открой %LOCALAPPDATA%\CELIKOM\Windows и удали session.dpapi вручную.',
            mbError, MB_OK);
      end;
    end;
  end;
end;
