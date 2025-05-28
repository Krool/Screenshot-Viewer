[Setup]
AppName=Game Screenshot Viewer
AppVersion=1.0
DefaultDirName={pf}\\Game Screenshot Viewer
DefaultGroupName=Game Screenshot Viewer
UninstallDisplayIcon={app}\\game_screenshots.exe
UninstallDisplayName=Game Screenshot Viewer
Compression=lzma
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=GameScreenshotViewerSetup

[Files]
Source: "dist\\game_screenshots.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "steam_games_cache.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "custom_games_cache.json"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\Game Screenshot Viewer"; Filename: "{app}\\game_screenshots.exe"
Name: "{commondesktop}\\Game Screenshot Viewer"; Filename: "{app}\\game_screenshots.exe"

[Run]
Filename: "{app}\\game_screenshots.exe"; Description: "Run Game Screenshot Viewer"; Flags: postinstall nowait skipifsilent

[Dirs]
Name: "{userappdata}\\Game Screenshot Viewer\\Logs"; Flags: uninsneveruninstall 