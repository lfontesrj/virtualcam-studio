; ============================================================
; VirtualCam Studio - Instalador Otimizado (Inno Setup)
; Instala o aplicativo + driver de câmera virtual
; Experiência plug-and-play: Next > Next > Install > Finish
; Versao otimizada: ~30-40 MB download, ~60-70 MB instalado
; ============================================================

#define MyAppName "VirtualCam Studio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "VirtualCam Studio"
#define MyAppURL "https://github.com/virtualcam-studio"
#define MyAppExeName "VirtualCamStudio.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=VirtualCamStudio_Setup_v{#MyAppVersion}
; SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
; Minimum Windows 11
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
; WizardImageFile=..\assets\wizard_image.bmp
; WizardSmallImageFile=..\assets\wizard_small.bmp

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
brazilianportuguese.InstallingOBS=Instalando driver de camera virtual...
brazilianportuguese.RegisteringDriver=Registrando driver de camera virtual...
brazilianportuguese.DriverInstalled=Driver de camera virtual instalado com sucesso!
brazilianportuguese.OBSNotFound=OBS Studio nao detectado. O driver sera instalado automaticamente.
english.InstallingOBS=Installing virtual camera driver...
english.RegisteringDriver=Registering virtual camera driver...
english.DriverInstalled=Virtual camera driver installed successfully!
english.OBSNotFound=OBS Studio not detected. The driver will be installed automatically.

[Types]
Name: "full"; Description: "Instalacao Completa (recomendado)"
Name: "compact"; Description: "Instalacao Compacta (sem OBS)"
Name: "custom"; Description: "Instalacao Personalizada"; Flags: iscustom

[Components]
Name: "main"; Description: "VirtualCam Studio (aplicativo principal)"; Types: full compact custom; Flags: fixed
Name: "templates"; Description: "Templates de overlay (exemplos)"; Types: full custom
Name: "samples"; Description: "Arquivos de exemplo (ticker, indicadores)"; Types: full custom
Name: "obs"; Description: "OBS Studio (driver de camera virtual)"; Types: full custom; ExtraDiskSpaceRequired: 524288000

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Iniciar com o Windows (minimizado)"; GroupDescription: "Opcoes adicionais:"; Flags: unchecked

[Files]
; === Main Application (PyInstaller output) ===
Source: "..\dist\VirtualCamStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main

; === Templates ===
Source: "..\assets\templates\*.png"; DestDir: "{app}\assets\templates"; Flags: ignoreversion; Components: templates

; === Sample Files ===
Source: "..\assets\sample_ticker.txt"; DestDir: "{app}\assets"; Flags: ignoreversion; Components: samples
Source: "..\assets\sample_indicators.txt"; DestDir: "{app}\assets"; Flags: ignoreversion; Components: samples
Source: "..\assets\sample_indicators.json"; DestDir: "{app}\assets"; Flags: ignoreversion; Components: samples

; === Driver Scripts ===
Source: "..\drivers\install_virtualcam.bat"; DestDir: "{app}\drivers"; Flags: ignoreversion; Components: main
Source: "..\drivers\uninstall_virtualcam.bat"; DestDir: "{app}\drivers"; Flags: ignoreversion; Components: main
Source: "..\drivers\install_obs_silent.ps1"; DestDir: "{app}\drivers"; Flags: ignoreversion; Components: obs

; === OBS Installer (bundled) ===
; NOTE: You need to place the OBS installer in the 'installer' folder before building
; Download from: https://obsproject.com/download
Source: "OBS-Studio-Full-Installer-x64.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall nocompression; Components: obs; Check: not IsOBSInstalled

; === License ===
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion; Components: main

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Abrir VirtualCam Studio"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Abrir VirtualCam Studio"

[Registry]
; Auto-start with Windows (optional)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VirtualCamStudio"; ValueData: """{app}\{#MyAppExeName}"" --minimized"; Flags: uninsdeletevalue; Tasks: startupicon

; App registration
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey

[Run]
; Install OBS silently if component selected and OBS not installed
Filename: "{tmp}\OBS-Studio-Full-Installer-x64.exe"; Parameters: "/S"; StatusMsg: "{cm:InstallingOBS}"; Flags: waituntilterminated; Components: obs; Check: not IsOBSInstalled

; Register virtual camera driver
Filename: "regsvr32"; Parameters: "/s ""{code:GetVCamDll64Path}"""; StatusMsg: "{cm:RegisteringDriver}"; Flags: waituntilterminated runhidden; Check: VCamDllExists

; Launch application
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Unregister virtual camera on uninstall (only if we installed it)
Filename: "regsvr32"; Parameters: "/s /u ""{code:GetVCamDll64Path}"""; Flags: runhidden; RunOnceId: "UnregVCam64"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\config"

[Code]
// ============================================================
// Pascal Script - Custom logic for the installer
// ============================================================

function IsOBSInstalled: Boolean;
begin
  Result := DirExists(ExpandConstant('{autopf}\obs-studio\bin\64bit'));
  if not Result then
    Result := DirExists(ExpandConstant('{autopf32}\obs-studio\bin\64bit'));
end;

function GetOBSDir: String;
begin
  if DirExists(ExpandConstant('{autopf}\obs-studio')) then
    Result := ExpandConstant('{autopf}\obs-studio')
  else if DirExists(ExpandConstant('{autopf32}\obs-studio')) then
    Result := ExpandConstant('{autopf32}\obs-studio')
  else
    Result := ExpandConstant('{autopf}\obs-studio');
end;

function GetVCamDll64Path(Param: String): String;
begin
  Result := GetOBSDir + '\data\obs-plugins\win-dshow\obs-virtualcam-module64.dll';
end;

function VCamDllExists: Boolean;
begin
  Result := FileExists(GetVCamDll64Path(''));
end;

// Show a custom page with setup summary
procedure InitializeWizard;
begin
  // The wizard is already configured via [Setup] section
  // Additional customization can be added here
end;

// Pre-installation checks
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  
  if CurPageID = wpSelectComponents then
  begin
    // If user deselected OBS component and OBS is not installed, warn them
    if not IsOBSInstalled and not WizardIsComponentSelected('obs') then
    begin
      if MsgBox(
        'Voce nao selecionou a instalacao do OBS Studio e ele nao esta ' +
        'instalado no seu sistema.' + #13#10 + #13#10 +
        'Sem o OBS, a camera virtual NAO funcionara.' + #13#10 + #13#10 +
        'Deseja continuar mesmo assim?',
        mbConfirmation, MB_YESNO) = IDNO then
      begin
        Result := False;
      end;
    end;
  end;
end;

// Post-installation: verify driver registration
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Try to register the virtual camera if OBS is now installed
    if VCamDllExists then
    begin
      Exec('regsvr32', '/s "' + GetVCamDll64Path('') + '"',
           '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      
      // Also try 32-bit
      if FileExists(GetOBSDir + '\data\obs-plugins\win-dshow\obs-virtualcam-module32.dll') then
      begin
        Exec('regsvr32', '/s "' + GetOBSDir + '\data\obs-plugins\win-dshow\obs-virtualcam-module32.dll"',
             '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;

// Cleanup on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Ask if user wants to remove settings
    DataDir := ExpandConstant('{userappdata}\VirtualCamStudio');
    if DirExists(DataDir) then
    begin
      if MsgBox(
        'Deseja remover tambem as configuracoes e dados do usuario?',
        mbConfirmation, MB_YESNO) = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;
