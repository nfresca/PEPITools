# PEPITools

Web para seguir el turf argentino desde cualquier navegador: el vivo de los
hipódromos, el programa de cada reunión y el calendario de carreras.

## Qué tiene

- **Hoy** — dos reproductores del vivo de YouTube lado a lado (uno por
  Chromecast, cada uno con su hipódromo) y el programa completo del día, con la
  próxima carrera resaltada y el PDF oficial para ver en el navegador
- **Programa** — cada carrera con horario, distancia, condición, bolsa y
  participantes (mandil, jockey, kilos, entrenador, últimas actuaciones). En
  las reuniones ya corridas muestra el marcador, los sports y el video de cada carrera
- **Calendario** — el mes actual y el siguiente de Palermo, San Isidro y La Plata,
  incluidas las reuniones confirmadas que todavía no tienen programa. Se imprime
  (o se guarda como PDF) en una hoja A4 apaisada
- **En la tele** — se castea con el botón Cast del reproductor de YouTube
  (Chrome en la PC o la app de YouTube en el celular)

Los datos salen de [studbook.org.ar](https://www.studbook.org.ar/reuniones).

## Cómo funciona

Es un sitio estático en GitHub Pages; no hay servidor.

1. `scraper/studbook.py` baja el calendario y los programas de studbook y los
   guarda como JSON en `site/data/`, junto con una copia de cada PDF (studbook
   los manda como descarga; servidos desde Pages se abren en el navegador)
2. El workflow `.github/workflows/pages.yml` corre el scraper cada hora (y en
   cada push) y publica la carpeta `site/`
3. `site/app.js` lee esos JSON y arma las vistas en el navegador

Se descargan programas completos solo de las reuniones entre 3 días atrás y 7
días adelante; el resto del calendario enlaza a studbook.

## Correrlo local

```bash
pip install -r requirements.txt
python scraper/studbook.py
python -m http.server -d site
```

y abrir <http://localhost:8000>.

## Publicarlo

En el repo de GitHub: **Settings → Pages → Source: GitHub Actions**. Después
de eso, cada push a `master` y cada hora se republica sola.
