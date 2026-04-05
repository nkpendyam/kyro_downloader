; Inno Setup Script for Kyro Downloader
; https://jrsoftware.org/isinfo.php

#define MyAppName "Kyro Downloader"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "nkpendyam"
#define MyAppURL "https://github.com/nkpendyam/kyro_downloader"
#define MyAppExeName "KyroDownloader.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist\windows
OutputBaseFilename=kyro_downloader_setup
SetupIconFile=..\..\src\gui\assets\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "contextmenu"; Description: "Add 'Download with Kyro' to Explorer context menu"; GroupDescription: "Shell Integration:"; Flags: checkedonce
Name: "fileassoc"; Description: "Associate .kyro files with Kyro Downloader"; GroupDescription: "File Associations:"; Flags: checkedonce
Name: "autostart"; Description: "Start Kyro Downloader on login"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Context menu integration
Root: HKCU; Subkey: "Software\Classes\*\shell\KyroDownload"; ValueType: string; ValueName: ""; ValueData: "Download with Kyro"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\KyroDownload"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\{#MyAppExeName}"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\KyroDownload\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: contextmenu
; File association for .kyro
Root: HKCU; Subkey: "Software\Classes\.kyro"; ValueType: string; ValueName: ""; ValueData: "KyroFile"; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\KyroFile"; ValueType: string; ValueName: ""; ValueData: "Kyro Download File"; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\KyroFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\KyroFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc
; Auto-start on login
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "KyroDownloader"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
