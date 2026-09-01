; Inno Setup — instalador de PEPITools.
; Requiere haber corrido antes:  pyinstaller --noconfirm PEPITools.spec
; Compilar:  ISCC.exe PEPITools.iss   ->  Output\PEPITools-Setup.exe

#define AppName    "PEPITools"
#define AppVersion "1.0.0"
#define AppExe     "PEPITools.exe"

[Setup]
AppId={{8F3A1C42-9B27-4E5D-A6F1-2D7C9E4B8A03}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=nfresca
AppSupportURL=https://github.com/nfresca/PEPITools
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; Instala para el usuario actual: no pide permisos de administrador. Es lo que
; conviene acá porque la app no toca nada del sistema.
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename={#AppName}-Setup
SetupIconFile=pepistream.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; \
    GroupDescription: "Accesos directos:"

[Files]
; Toda la carpeta que genera PyInstaller.
Source: "dist\PEPITools\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExe}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Los datos del usuario (presets, calendario, caché, yt-dlp y ffmpeg
; descargados) viven acá, fuera de la carpeta de instalación. Se borran solo al
; desinstalar; una actualización los conserva.
Type: filesandordirs; Name: "{localappdata}\PEPITools"
