[Setup]
AppName=Game Screenshot Viewer
AppVersion=1.0.0
AppPublisher=Your Name
AppPublisherURL=https://example.com
AppSupportURL=https://example.com/support
AppUpdatesURL=https://example.com/updates
DefaultDirName={autopf}\Game Screenshot Viewer
DefaultGroupName=Game Screenshot Viewer
OutputDir=installer
OutputBaseFilename=GameScreenshotViewer_Setup_1.0.0
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\app_icon.ico
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
DisableWelcomePage=no
MinVersion=6.1sp1
PrivilegesRequired=lowest

[Files]
Source: "dist\Game Screenshot Viewer\Game Screenshot Viewer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Game Screenshot Viewer\steam_games_cache.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Game Screenshot Viewer\custom_games_cache.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Game Screenshot Viewer\app_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Game Screenshot Viewer"; Filename: "{app}\Game Screenshot Viewer.exe"; IconFilename: "{app}\app_icon.ico"
Name: "{autodesktop}\Game Screenshot Viewer"; Filename: "{app}\Game Screenshot Viewer.exe"; IconFilename: "{app}\app_icon.ico"

[Run]
Filename: "{app}\Game Screenshot Viewer.exe"; Description: "Run Game Screenshot Viewer"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\*.log"

[Dirs]
Name: "{userappdata}\Game Screenshot Viewer\Logs"; Flags: uninsneveruninstall 