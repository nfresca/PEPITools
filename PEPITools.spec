# PyInstaller — receta de empaquetado de PEPITools.
#   Build:  pyinstaller --noconfirm PEPITools.spec
# Genera dist/PEPITools/ (modo carpeta: arranca al instante y es lo que
# after espera un instalador). El instalador se arma con PEPITools.iss.

import os

# El .ico no está versionado (la app lo genera sola al arrancar), así que en un
# clon limpio o en CI no existe. Se genera acá desde el PNG para que el build
# sea reproducible en cualquier máquina.
ICON = "pepistream.ico"
if not os.path.isfile(ICON):
    from PIL import Image
    _src = Image.open("Diseño sin título.png").convert("RGBA")
    _sizes = [16, 32, 48, 64, 128, 256]
    _frames = [_src.resize((s, s), Image.LANCZOS) for s in _sizes]
    _frames[0].save(ICON, format="ICO", sizes=[(s, s) for s in _sizes],
                    append_images=_frames[1:])

# pychromecast y zeroconf resuelven módulos en tiempo de ejecución, así que
# PyInstaller no los detecta solos: sin declararlos, el .exe compila bien pero
# después no encuentra ningún Chromecast.
hiddenimports = [
    "pychromecast",
    "pychromecast.controllers",
    "pychromecast.controllers.media",
    "zeroconf",
    "zeroconf._utils.ipaddress",
    "zeroconf._handlers.answers",
    "casttube",
    "bs4",
    "requests",
    "PIL.Image",
    "PIL.ImageTk",
]

a = Analysis(
    ["transmiturf.py"],
    pathex=[],
    binaries=[],
    # Solo recursos de LECTURA. Los datos que la app escribe (presets,
    # calendario, caché, yt-dlp.exe, ffmpeg.exe, logs) viven en
    # %LOCALAPPDATA%\PEPITools — ver _data_dir() en transmiturf.py.
    datas=[("Diseño sin título.png", ".")],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas", "pytest", "PyInstaller"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="PEPITools",
    debug=False,
    strip=False,
    upx=False,
    console=False,          # app de ventana: sin consola negra detrás
    icon="pepistream.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PEPITools",
)
