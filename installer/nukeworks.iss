#define MyAppName "NukeWorks"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#ifndef MyAppPublisher
  #define MyAppPublisher "NukeWorks"
#endif
#ifndef MyAppURL
  #define MyAppURL "https://example.com/nukeworks"
#endif

[Setup]
AppId={{C9E5F4C5-0CD5-428E-9FF4-9F69AF2DAE58}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename={#MyAppName}-{#MyAppVersion}-Setup
OutputDir={#SourcePath}\out
ArchitecturesInstallIn64BitMode=x64
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
SetupLogging=yes
UninstallDisplayIcon={app}\NukeWorks.exe
WizardStyle=modern
CloseApplications=force
RestartIfNeededByRun=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\NukeWorks\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Dirs]
Name: "{app}\logs"; Flags: uninsneveruninstall
Name: "{app}\uploads"; Flags: uninsneveruninstall
Name: "{app}\flask_sessions"; Flags: uninsneveruninstall

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\NukeWorks.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\NukeWorks.exe"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\NukeWorks.exe"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
