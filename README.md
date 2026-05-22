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
- **Auto-instalación** — instala todas las dependencias automáticamente en el primer arranque

---

## Requisitos

- Windows 10/11
- [Python 3.12+](https://python.org) (el launcher lo instala automáticamente si no está)
- [VLC media player](https://www.videolan.org/vlc/) instalado en la ruta por defecto (`C:\Program Files\VideoLAN\VLC\`)
- Red local con Chromecast

---

## Instalación y uso

1. Descargá o cloná este repositorio
2. Hacé doble clic en **`PEPITools.bat`**
3. En el primer arranque se instalan automáticamente: `pychromecast`, `Pillow`, `requests`, `beautifulsoup4` y `yt-dlp`
4. Seleccioná un hipódromo o pegá cualquier URL de YouTube
5. Hacé clic en **↻** para buscar Chromecasts en tu red
6. Seleccioná los dispositivos y presioná **Transmitir**

---

## Tecnologías

| Herramienta | Uso |
|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Extrae la URL del stream de YouTube |
| [VLC](https://www.videolan.org/vlc/) | Transmite el stream al Chromecast |
| [pychromecast](https://github.com/balloob/pychromecast) | Descubrimiento de dispositivos Chromecast en la red |
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
