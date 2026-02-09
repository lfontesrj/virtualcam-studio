; VirtualCam Studio - Inno Setup Script
; Gera o instalador .exe para Windows 11

[Setup]
AppName=VirtualCam Studio
AppVersion=1.0.0
AppPublisher=VirtualCam Studio
AppPublisherURL=https://github.com/virtualcam-studio
DefaultDirName={autopf}\VirtualCam Studio
DefaultGroupName=VirtualCam Studio
OutputDir=..\dist\installer
OutputBaseFilename=VirtualCamStudio_Setup_v1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=..\assets\icons\app_icon.ico
UninstallDisplayIcon={app}\VirtualCamStudio.exe
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
; Windows 11 minimum

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na &Area de Trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "startupicon"; Description: "Iniciar com o &Windows"; GroupDescription: "Opcoes:"; Flags: unchecked

[Files]
; Main application files (from PyInstaller output)
Source: "..\dist\VirtualCamStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Assets
Source: "..\assets\templates\*.png"; DestDir: "{app}\assets\templates"; Flags: ignoreversion
Source: "..\assets\sample_ticker.txt"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\sample_indicators.txt"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\sample_indicators.json"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\VirtualCam Studio"; Filename: "{app}\VirtualCamStudio.exe"
Name: "{group}\Desinstalar VirtualCam Studio"; Filename: "{uninstallexe}"
Name: "{autodesktop}\VirtualCam Studio"; Filename: "{app}\VirtualCamStudio.exe"; Tasks: desktopicon

[Registry]
; Auto-start with Windows (optional)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VirtualCamStudio"; ValueData: """{app}\VirtualCamStudio.exe"" --minimized"; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
Filename: "{app}\VirtualCamStudio.exe"; Description: "Iniciar VirtualCam Studio"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;

  // Check if OBS is installed
  if not FileExists(ExpandConstant('{autopf}\obs-studio\bin\64bit\obs64.exe')) then
  begin
    if MsgBox(
      'O OBS Studio nao foi detectado no seu sistema.' + #13#10 +
      'O OBS e necessario para o driver de camera virtual.' + #13#10 + #13#10 +
      'Deseja continuar a instalacao mesmo assim?' + #13#10 +
      '(Voce pode instalar o OBS depois)',
      mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;
