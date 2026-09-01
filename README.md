# PEPITools

Aplicación de escritorio para Windows que transmite el stream en vivo de los hipódromos argentinos directamente a dispositivos **Chromecast**, sin necesidad de abrir un navegador.

---

## Características

- **Transmisión a Chromecast** — envía el stream a uno o varios dispositivos Chromecast en tu red local simultáneamente
- **Presets de hipódromos** — acceso rápido a Palermo, San Isidro y La Plata con un solo clic
- **Detección automática de dispositivos** — escanea la red y lista todos los Chromecasts disponibles
- **Hipódromo del día** — muestra automáticamente qué hipódromo corre hoy y sus horarios (datos de [turfpremium.com.ar](https://turfpremium.com.ar))
- **Calendario mensual** — visualización del mes con colores por hipódromo
- **Programa oficial** — abre el PDF del programa del día con un clic
- **Ir al vivo** — reconecta el stream desde el inicio para eliminar el retraso acumulado
- **Sin dependencias que instalar** — el instalador trae todo; `yt-dlp` y `ffmpeg` se descargan solos en el primer arranque y `yt-dlp` se mantiene actualizado

---

## Requisitos

- Windows 10/11 (64 bits)
- Red local con Chromecast
- Conexión a internet en el primer arranque (descarga `yt-dlp` y `ffmpeg`)

No hace falta instalar Python ni VLC.

---

## Instalación

1. Descargá **`PEPITools-Setup.exe`** desde [Releases](https://github.com/nfresca/PEPITools/releases)
2. Ejecutalo. No pide permisos de administrador: se instala solo para tu usuario
3. Abrí PEPITools desde el escritorio o el menú de inicio

En el primer arranque descarga `yt-dlp` y `ffmpeg` (~120 MB en total). Puede
tardar unos minutos según la conexión; después ya no vuelve a hacerlo.

### Uso

1. Seleccioná un hipódromo o pegá cualquier URL de YouTube en el link manual
2. Hacé clic en **↻** para buscar Chromecasts en tu red
3. Seleccioná los dispositivos y presioná **Transmitir**

### Dónde guarda sus datos

Los presets, el calendario, la caché y los binarios descargados van a
`%LOCALAPPDATA%\PEPITools`. Se conservan al actualizar y se borran al
desinstalar.

---

## Ejecutar desde el código fuente

```bash
pip install -r requirements.txt
python transmiturf.py
```

O hacé doble clic en `PEPITools.bat`, que instala Python si falta.

## Compilar el instalador

Necesita [Inno Setup 6](https://jrsoftware.org/isinfo.php):

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm PEPITools.spec
ISCC.exe PEPITools.iss          # genera Output\PEPITools-Setup.exe
```

También se compila solo en GitHub Actions al publicar un tag (`v*`).

---

## Tecnologías

| Herramienta | Uso |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Extrae la URL del stream de YouTube |
| [ffmpeg](https://ffmpeg.org/) | Reempaqueta el stream a MP4 fragmentado (sin recodificar) |
| [pychromecast](https://github.com/balloob/pychromecast) | Descubre los Chromecast y controla la reproducción |
| [tkinter](https://docs.python.org/3/library/tkinter.html) | Interfaz gráfica |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | Scraping del calendario de carreras |

---

## Hipódromos soportados

| Hipódromo | Stream |
|---|---|
| Hipódromo de Palermo | YouTube oficial |
| Hipódromo de San Isidro | YouTube oficial |
| Hipódromo de La Plata | YouTube oficial |

Las URLs de stream se pueden configurar desde el botón **⚙** dentro de la app.
