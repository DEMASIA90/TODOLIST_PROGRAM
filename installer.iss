; Auto Todo Desktop - Inno Setup
#define MyAppName "Auto Todo Desktop"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Local"
#define MyAppExeName "AutoTodoDesktop.exe"

[Setup]
AppId={{B5D1B12A-3C68-47C2-B42D-72C8579C5820}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\AutoTodoDesktop
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=AutoTodoDesktop_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "바탕 화면 바로가기 만들기"; GroupDescription: "추가 아이콘:"; Flags: unchecked
Name: "startup"; Description: "Windows 로그인 시 자동 실행"; GroupDescription: "자동 실행:"; Flags: checkedonce

[Files]
Source: "dist_onedir\AutoTodoDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} 실행"; Flags: nowait postinstall skipifsilent
