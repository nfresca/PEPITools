"""Scrapea calendario y programas de studbook.org.ar y los deja como JSON.

Genera, dentro de la carpeta de salida (por defecto site/data):
  calendario.json        reuniones del mes actual y el siguiente
  reuniones/<id>.json    programa (o resultados) de cada reunión cercana a hoy

Uso: python scraper/studbook.py [carpeta_salida]
"""

import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.studbook.org.ar"
TZ = timezone(timedelta(hours=-3), "ART")  # Argentina no usa horario de verano
# Reuniones con programa completo: desde DIAS_ATRAS antes de hoy hasta DIAS_ADELANTE después.
DIAS_ATRAS, DIAS_ADELANTE = 3, 7
# Solo estos hipódromos (nombre como aparece en studbook); el resto se ignora.
HIPODROMOS = {"Palermo", "San Isidro", "La Plata"}

# Sin un User-Agent de navegador, studbook responde 403.
session = requests.Session()
session.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"),
    "Accept-Language": "es-AR,es;q=0.9",
})


def get_soup(path: str) -> BeautifulSoup:
    r = session.get(BASE + path, timeout=30)
    r.raise_for_status()
    # El sitio mezcla UTF-8 con algunos bytes Latin-1 sueltos (nombres de días).
    return BeautifulSoup(r.content.decode("utf-8", errors="replace"), "html.parser")


def texto(el) -> str:
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def color_de(style: str, prop: str) -> str | None:
    m = re.search(prop + r"\s*:\s*(#[0-9a-fA-F]{3,6}|[a-z]+)", style or "")
    return m.group(1) if m else None


# ── Calendario ────────────────────────────────────────────────────────────────

def scrape_mes(anio: int, mes: int) -> list[dict]:
    soup = get_soup(f"/reuniones?anio={anio}&mes={mes:02d}")
    reuniones = []
    for td in soup.select("td.box-dia[data-dia]"):
        fecha = date(int(td["data-anio"]), int(td["data-mes"]), int(td["data-dia"]))
        for caja in td.select(".box-hipo"):
            hipodromo = texto(caja.select_one(".label"))
            if hipodromo not in HIPODROMOS:
                continue
            # Las reuniones futuras sin programa publicado vienen sin link a su detalle.
            a = caja.find_parent("a", href=re.compile(r"^/reuniones/detalle/\d+/"))
            circulo = caja.select_one(":scope > div")
            nums = [int(n) for n in re.findall(r"\d+", texto(caja.select_one(".box-dato")))]
            reuniones.append({
                "id": int(re.search(r"\d+", a["href"]).group()) if a else None,
                "fecha": fecha.isoformat(),
                "hipodromo": hipodromo,
                "sigla": texto(circulo),
                "color": color_de(circulo.get("style") if circulo else "", "color"),
                "carreras": nums[0] if nums else None,
                "anotados": nums[1] if len(nums) > 1 else None,
                "url": BASE + (a["href"] if a else f"/reuniones?anio={anio}&mes={mes:02d}"),
            })
    return reuniones


# ── Programa de una reunión ──────────────────────────────────────────────────

def _celda(celdas, headers, nombre, despues_de=None):
    """Celda bajo la columna `nombre`; con `despues_de`, la primera tras esa columna
    (la tabla repite cabeceras como 'P' y 'Kg')."""
    inicio = headers.index(despues_de) + 1 if despues_de in headers else 0
    try:
        i = headers.index(nombre, inicio)
    except ValueError:
        return None
    return celdas[i] if i < len(celdas) else None


def _link(td, fragmento):
    a = td.select_one(f"a[href*='{fragmento}']") if td else None
    return texto(a) or None


def _participante(tr, headers, resultados: bool) -> dict:
    celdas = tr.find_all("td", recursive=False)
    gatera = tr.select_one("td.orden-gatera")
    ejemplar = _celda(celdas, headers, "Ejemplar")
    p = {
        "numero": texto(gatera),
        "mandil": color_de(gatera.get("style") if gatera else "", "background-color"),
        "mandil_texto": color_de(gatera.span.get("style") if gatera and gatera.span else "", "color"),
        "nombre": texto(ejemplar.strong) if ejemplar else "",
        "padres": texto(ejemplar.select_one("span.small")) or None if ejemplar else None,
        "jockey": _link(tr, "/jockey/"),
        "kg": texto(_celda(celdas, headers, "Kg", despues_de="Jockey")) or None,
        "entrenador": _link(tr, "/entrenador/"),
        "caballeriza": _link(tr, "/caballerizas/"),
    }
    if resultados:
        p["puesto"] = texto(celdas[0]) or None
        p["cuerpos"] = texto(_celda(celdas, headers, "Cpos")) or None
        p["pago"] = texto(_celda(celdas, headers, "Pago")) or None
    else:
        p["ultimas"] = " ".join(texto(a) for a in celdas[0].select("a.performance")) or texto(celdas[0].strong) or None
    return p


def _carrera(h2) -> dict:
    """Arma una carrera a partir de su título <h2 id="rN"> y lo que sigue hasta la próxima."""
    numero = int(h2["id"][1:])
    nodos = []
    for sib in h2.find_parent("div", class_="row").find_next_siblings():
        if sib.find(id=re.compile(r"^r\d+$")):
            break
        nodos.append(sib)
    cabecera = h2.find_parent("div", class_="carrera-cabecera-info")
    bloque = [cabecera] + nodos

    def buscar(sel):
        for n in bloque:
            el = n.select_one(sel)
            if el:
                return el
        return None

    video = cabecera.select_one("[data-video]")
    distancia = re.search(r"(\d+)\s*mts", texto(buscar(".carrera-cabecera-distancia")))
    condicion = cabecera.find("strong", string=re.compile("Condici"))
    tabla = None
    resultados = False
    for n in nodos:
        titulo = n.select_one(".carrera-encabezado-resumen h3")
        if titulo:
            resultados = "RESULTADO" in texto(titulo).upper()
        t = n.select_one("table.data")
        if t:
            tabla = t
            break

    participantes = []
    if tabla:
        headers = [texto(th) for th in tabla.select("thead th")]
        headers = [h.split(" (")[0] for h in headers]  # "8 últimas (días s/c)" → "8 últimas"
        for tr in tabla.select("tbody > tr"):
            if tr.select_one("td.orden-gatera"):
                participantes.append(_participante(tr, headers, resultados))

    return {
        "numero": numero,
        "hora": texto(h2.select_one(".carrera-cabecera-hora")) or None,
        "premio": texto(cabecera.select_one(".carrera-cabecera-premio-nombre")) or None,
        "distancia": int(distancia.group(1)) if distancia else None,
        "pista": texto(buscar(".carrera-cabecera-metadato-pista .carrera-cabecera-metadato-valor")) or None,
        "categoria": texto(buscar(".carrera-cabecera-metadato-categoria .carrera-cabecera-metadato-valor")) or None,
        "condicion": texto(condicion.parent).removeprefix("Condición:").strip() if condicion else None,
        "bolsa": (texto(buscar(".carrera-premios-titulo-principal .p-peso")).strip("()").removeprefix("Bolsa:").strip() or None),
        "video": video["data-video"] if video else None,
        "resultados": resultados,
        "participantes": participantes,
    }


def scrape_reunion(reunion: dict) -> dict:
    soup = get_soup(reunion["url"].removeprefix(BASE))
    titulo = texto(soup.select_one("h3.reunion"))
    pdf = soup.select_one("a[href^='/reuniones/detalle-pdf/']")
    num = re.search(r"\d+", titulo)
    return {
        **reunion,
        "numero_reunion": int(num.group()) if num else None,
        "pdf": BASE + pdf["href"] if pdf else None,
        "carreras_detalle": [_carrera(h2) for h2 in soup.select("h2.carrera-cabecera-titulo[id]")],
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    salida = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent.parent / "site" / "data")
    (salida / "reuniones").mkdir(parents=True, exist_ok=True)

    hoy = datetime.now(TZ).date()
    siguiente = (hoy.replace(day=28) + timedelta(days=4)).replace(day=1)
    meses = [(hoy.year, hoy.month), (siguiente.year, siguiente.month)]
    if hoy.day <= DIAS_ATRAS:  # la ventana de días cae en el mes anterior
        anterior = hoy.replace(day=1) - timedelta(days=1)
        meses.insert(0, (anterior.year, anterior.month))

    reuniones = []
    for anio, mes in meses:
        reuniones += scrape_mes(anio, mes)
        time.sleep(1)

    desde, hasta = hoy - timedelta(days=DIAS_ATRAS), hoy + timedelta(days=DIAS_ADELANTE)
    errores = 0
    for r in reuniones:
        if r["id"] is None or not desde <= date.fromisoformat(r["fecha"]) <= hasta:
            continue
        try:
            detalle = scrape_reunion(r)
        except Exception as e:  # una reunión rota no debe tirar abajo el resto
            errores += 1
            print(f"ERROR reunión {r['id']} ({r['fecha']} {r['hipodromo']}): {e}", file=sys.stderr)
            continue
        r["programa"] = True
        (salida / "reuniones" / f"{r['id']}.json").write_text(
            json.dumps(detalle, ensure_ascii=False), encoding="utf-8")
        print(f"{r['fecha']} {r['hipodromo']}: {len(detalle['carreras_detalle'])} carreras")
        time.sleep(1)

    (salida / "calendario.json").write_text(json.dumps({
        "actualizado": datetime.now(TZ).isoformat(timespec="minutes"),
        "reuniones": reuniones,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(reuniones)} reuniones en calendario, {errores} errores")
    if not reuniones:
        sys.exit("El calendario vino vacío: probablemente cambió el HTML de studbook")


if __name__ == "__main__":
    main()
