#!/usr/bin/env python3
"""
PEPITools — YouTube → Chromecast (directo, sin VLC)
Multi-Chromecast + Presets de Hipódromos de Argentina.
Se auto-configura en el primer arranque.
"""

import os, sys, json, shutil, importlib, threading, subprocess, urllib.request, webbrowser
import tkinter as tk
from tkinter import ttk

APP_DIR        = os.path.dirname(os.path.abspath(__file__))
VLC_PATH       = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
YTDLP_URL      = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
YTDLP_LOCAL    = os.path.join(APP_DIR, "yt-dlp.exe")
CAT_IMG        = os.path.join(APP_DIR, "Diseño sin título.png")
PRESETS_FILE   = os.path.join(APP_DIR, "presets.json")
CALENDAR_FILE  = os.path.join(APP_DIR, "calendario.json")
NO_WINDOW      = subprocess.CREATE_NO_WINDOW

DIAS_ES  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
DIAS_SHORT = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]

CACHE_FILE  = os.path.join(APP_DIR, "calendario_cache.json")
CACHE_HOURS = 6

HIPO_COLORS = {
    "Hipódromo de Palermo":    "#ec407a",   # rosa
    "Hipódromo de San Isidro": "#43a047",   # verde oscuro
    "Hipódromo de La Plata":   "#039be5",   # celeste oscuro
}
HIPO_ABBREV = {
    "Hipódromo de Palermo":    "Palermo",
    "Hipódromo de San Isidro": "San Isidro",
    "Hipódromo de La Plata":   "La Plata",
}
HIPO_WEBSITES = {
    "Hipódromo de Palermo":    "https://old.palermo.com.ar/es/turf/calendario-de-carreras",
    "Hipódromo de San Isidro": "https://hipodromosanisidro.com/programas/",
    "Hipódromo de La Plata":   "https://www.hipodromolaplata.gba.gov.ar/ns2012/ih_Infohipica/ih_000InfoHipica.php#",
}

DEFAULT_PRESETS = [
    {"name": "Hipódromo de Palermo",    "url": ""},
    {"name": "Hipódromo de San Isidro", "url": ""},
    {"name": "Hipódromo de La Plata",   "url": ""},
]

# ── paleta Steam ──────────────────────────────────────────────────────────────
BG_DARK    = "#171a21"   # fondo principal
BG_CARD    = "#1e2328"   # tarjetas
BG_ENTRY   = "#2a475e"   # campos de texto
ACCENT     = "#1a9fff"   # azul Steam
ACCENT_H   = "#0d86e3"   # hover
ACCENT_D   = "#0a3a5c"   # deshabilitado
PRESET_BG  = "#2a475e"
PRESET_SEL = "#1a9fff"
TEXT       = "#c6d4df"   # texto Steam
MUTED      = "#8f98a0"   # texto secundario Steam
OK_CLR     = "#57cbde"   # cyan claro
ERR_CLR    = "#ff4848"
WARN_CLR   = "#e8a838"   # ámbar
STATUS_BG  = "#101318"
SEP_CLR    = "#2a475e"
RING_CLR   = (26, 159, 255)  # azul Steam para el anillo del logo


# ── presets I/O ───────────────────────────────────────────────────────────────
def _load_presets() -> list:
    try:
        with open(PRESETS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) == 3:
            return data
    except Exception:
        pass
    _save_presets(DEFAULT_PRESETS)
    return [dict(p) for p in DEFAULT_PRESETS]


def _save_presets(presets: list):
    with open(PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, ensure_ascii=False, indent=2)


def _load_calendar() -> dict:
    try:
        with open(CALENDAR_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        cal = {str(i): "" for i in range(7)}
        _save_calendar(cal)
        return cal


def _save_calendar(cal: dict):
    with open(CALENDAR_FILE, "w", encoding="utf-8") as f:
        json.dump(cal, f, ensure_ascii=False, indent=2)


TURFPREMIUM_PROGRA = "https://turfpremium.com.ar/web/web/gral/progra/index.php?idi=es"
TURFPREMIUM_LOGIN  = "https://turfpremium.com.ar/web/web/sesiones/loginvi.php?vis=1"
TURFPREMIUM_MAP    = {
    "SI": "Hipódromo de San Isidro",
    "Pa": "Hipódromo de Palermo",
    "LP": "Hipódromo de La Plata",
}
SCRAPE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def _load_race_cache() -> dict | None:
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            c = json.load(f)
        from datetime import datetime, timedelta
        if datetime.now() - datetime.fromisoformat(c["fetched_at"]) < timedelta(hours=CACHE_HOURS):
            return c
    except Exception:
        pass
    return None


def _save_race_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _fetch_race_calendar() -> dict:
    """
    Scrape turfpremium.com.ar/progra para obtener hipódromo por fecha.
    Devuelve {YYYY-MM-DD: nombre_hipódromo}.
    Requiere visitor login previo (sin contraseña).
    """
    import requests, re
    from bs4 import BeautifulSoup
    from datetime import date

    result = {}
    try:
        s = requests.Session()
        s.headers["User-Agent"] = SCRAPE_UA
        s.get(TURFPREMIUM_LOGIN, timeout=10)          # sesión de visitante
        r = s.get(TURFPREMIUM_PROGRA, timeout=15)
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", class_="menuprogint"):
            href  = a.get("href", "")
            m     = re.search(r"idfec=(\d{4})/(\d{1,2})/(\d{1,2})", href)
            parts = a.get_text(" ", strip=True).split()
            abbr  = parts[-1].strip() if parts else ""
            name  = TURFPREMIUM_MAP.get(abbr, "")
            if m and name:
                try:
                    result[date(int(m.group(1)),
                                int(m.group(2)),
                                int(m.group(3))).isoformat()] = name
                except ValueError:
                    pass
    except Exception:
        pass

    return result


def _calendar_summary(races: dict) -> str:
    """Texto de estado: cuántos días de Palermo/La Plata se encontraron."""
    from datetime import date
    today = date.today()
    counts: dict = {}
    for iso, name in races.items():
        try:
            d = date.fromisoformat(iso)
            if (d.year == today.year and d.month == today.month
                    and "isidro" not in name.lower()):
                ab = HIPO_ABBREV.get(name, name)
                counts[ab] = counts.get(ab, 0) + 1
        except ValueError:
            pass
    if not counts:
        return "sin datos confirmados de turfpremium — usando San Isidro por defecto"
    return "  ·  ".join(f"{n}: {c} días" for n, c in counts.items())






def _san_isidro_programa_pdf(today) -> str:
    """
    Busca el PDF del Programa Oficial de San Isidro para la fecha dada.
    API: hipodromosanisidro.com/wacP/public/...
    """
    import re, requests
    from bs4 import BeautifulSoup

    try:
        # 1. Obtener eventos del mes para encontrar el calendario_id de hoy
        yr, mo = today.year, today.month
        next_yr, next_mo = (yr, mo + 1) if mo < 12 else (yr + 1, 1)
        cal_url = (f"https://hipodromosanisidro.com/wacP/public/calendario"
                   f"?start={yr}-{mo:02d}-01&end={next_yr}-{next_mo:02d}-01")
        r    = requests.get(cal_url, headers={"User-Agent": SCRAPE_UA}, timeout=15)
        events = r.json()

        today_iso = today.isoformat()   # "2026-05-22"
        cal_id = None
        for ev in events:
            class_val = ev.get("className", "")
            has_prog = ("programa-oficial" in class_val
                        if isinstance(class_val, str)
                        else any("programa-oficial" in c for c in class_val))
            if ev.get("start") == today_iso and has_prog:
                # URL: "programa-oficial/?calendario_id=39661345"
                m = re.search(r"calendario_id=(\d+)", ev.get("url", ""))
                if m:
                    cal_id = m.group(1)
                    break

        if not cal_id:
            return ""

        # 2. Obtener el HTML del programa de ese día y buscar el PDF
        r2   = requests.get(
            f"https://hipodromosanisidro.com/wacP/public/programa-oficial/{cal_id}",
            headers={"User-Agent": SCRAPE_UA}, timeout=15
        )
        soup = BeautifulSoup(r2.text, "html.parser")

        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True).upper()
            if "PROGRAMA OFICIAL" in text:
                href = a["href"]
                if not href.startswith("http"):
                    href = "https://hipodromosanisidro.com" + href
                return href

    except Exception:
        pass
    return ""


def _palermo_programa_pdf(today) -> str:
    """
    Busca el PDF del programa oficial de Palermo para la fecha dada.
    Fuente: old.palermo.com.ar/es/turf/programa-oficial
    Devuelve la URL del PDF o cadena vacía si no se encuentra.
    """
    import re, requests
    from bs4 import BeautifulSoup

    try:
        r = requests.get(
            "https://old.palermo.com.ar/es/turf/programa-oficial",
            headers={"User-Agent": SCRAPE_UA}, timeout=15
        )
        soup = BeautifulSoup(r.text, "html.parser")

        # Cada fila tiene: <td>Programa oficial - Sabado 23 de mayo de 2026</td>
        # y luego un <a href=".../programa-oficial-reunion/ID">
        target = f"{today.day} de {MESES_ES[today.month - 1]} de {today.year}"

        for row in soup.find_all("tr"):
            td = row.find("td", class_="tabla_hora")
            if not td or target not in td.get_text(strip=True).lower():
                continue
            a = row.find("a", href=re.compile(r"programa-oficial-reunion/\d+"))
            if not a:
                continue
            # Entrar a la página de esa reunión y obtener el PDF específico
            r2   = requests.get(a["href"], headers={"User-Agent": SCRAPE_UA}, timeout=15)
            soup2 = BeautifulSoup(r2.text, "html.parser")
            pdf_a = soup2.find("a", href=re.compile(r"app_programa_oficial.*\.pdf"))
            if pdf_a:
                return pdf_a["href"]
    except Exception:
        pass
    return ""


def _preset_website(name: str) -> str:
    return HIPO_WEBSITES.get(name, "")


# ── estilos ttk ───────────────────────────────────────────────────────────────
def _apply_styles():
    s = ttk.Style()
    s.theme_use("default")
    s.configure("P.TCombobox",
                fieldbackground=BG_ENTRY, background=BG_CARD,
                foreground=TEXT, selectbackground=ACCENT,
                selectforeground="#000", relief="flat")
    s.map("P.TCombobox", fieldbackground=[("readonly", BG_ENTRY)])


# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PEPITools")
        self.geometry("600x660")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)

        _apply_styles()

        self._presets:   list = _load_presets()
        self._calendar:  dict = _load_calendar()
        self._casts:     dict = {}   # name → ip
        self._cast_vars: dict = {}   # name → BooleanVar
        self._ready:        bool = False
        self._logo_photo         = None
        self._wm_photo           = None
        self._selected_preset: int = -1
        self._ytdlp_proc: subprocess.Popen | None = None
        self._cancelled:  bool = False
        self._active_cast_names: list = []  # nombres de los Chromecasts en sesión activa
        self._vlc_procs:        list = []   # procesos VLC activos
        self._current_url:  str  = ""       # URL usada en la última transmisión

        self._build_ui()
        self._lock_controls()
        threading.Thread(target=self._auto_setup, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):

        # ── encabezado ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_DARK)
        hdr.pack(fill="x", padx=18, pady=(18, 8))

        self._logo_lbl = tk.Label(hdr, bg=BG_DARK)
        self._logo_lbl.pack(side="left", padx=(0, 12))

        col = tk.Frame(hdr, bg=BG_DARK)
        col.pack(side="left")
        tk.Label(col, text="PEPITools", bg=BG_DARK, fg=ACCENT,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(col, text="YouTube  ▸  Chromecast", bg=BG_DARK, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")

        # ── sección HOY ───────────────────────────────────────────────────────
        from datetime import date as _dt
        _today = _dt.today()
        _fecha = f"{DIAS_ES[_today.weekday()]} {_today.day} de {MESES_ES[_today.month-1]}"

        hoy_card = tk.Frame(self, bg=BG_CARD)
        hoy_card.pack(fill="x", padx=18, pady=(0, 4))

        # ── fila superior: fecha + botones ────────────────────────────────────
        top = tk.Frame(hoy_card, bg=BG_CARD)
        top.pack(fill="x", padx=14, pady=(10, 4))

        tk.Label(top, text=_fecha.upper(), bg=BG_CARD, fg=MUTED,
                 font=("Segoe UI", 10, "bold")).pack(side="left")

        btn_row = tk.Frame(top, bg=BG_CARD)
        btn_row.pack(side="right")
        tk.Button(btn_row, text="📄 Programa",
                  bg=BG_DARK, fg=TEXT,
                  activebackground="#1a1a1a", activeforeground=ACCENT,
                  relief="flat", cursor="hand2", font=("Segoe UI", 10),
                  padx=10, pady=5,
                  command=self._open_programa_thread).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="📅 Calendario",
                  bg=BG_DARK, fg=TEXT,
                  activebackground="#1a1a1a", activeforeground=ACCENT,
                  relief="flat", cursor="hand2", font=("Segoe UI", 10),
                  padx=10, pady=5,
                  command=self._open_month_calendar).pack(side="left")

        # ── fila inferior: hipódromo + horarios ──────────────────────────────
        bot = tk.Frame(hoy_card, bg=BG_CARD)
        bot.pack(fill="x", padx=16, pady=(4, 12))

        self._hoy_lbl = tk.Label(bot, text="Cargando…", bg=BG_CARD, fg=MUTED,
                                  font=("Segoe UI", 16, "bold"))
        self._hoy_lbl.pack(anchor="w")

        self._hoy_hours_lbl = tk.Label(bot, text="", bg=BG_CARD, fg=MUTED,
                                        font=("Segoe UI", 11))
        self._hoy_hours_lbl.pack(anchor="w")

        # ── tarjeta principal ─────────────────────────────────────────────────
        card = tk.Frame(self, bg=BG_CARD)
        card.pack(fill="x", padx=18, pady=(0, 6), ipady=2)

        # —— sección presets ——————————————————————————————————————————————————
        phdr = tk.Frame(card, bg=BG_CARD)
        phdr.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(phdr, text="HIPÓDROMOS", bg=BG_CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        cfg_btn = tk.Button(phdr, text="⚙", bg=BG_CARD, fg=MUTED,
                            activebackground=BG_DARK, activeforeground=ACCENT,
                            relief="flat", cursor="hand2",
                            font=("Segoe UI", 13),
                            command=self._open_preset_dialog)
        cfg_btn.pack(side="right")
        _hover(cfg_btn, MUTED, ACCENT, BG_CARD, BG_DARK)

        preset_row = tk.Frame(card, bg=BG_CARD)
        preset_row.pack(fill="x", padx=16, pady=(0, 12))

        self._preset_btns: list[tk.Button] = []
        for i, p in enumerate(self._presets):
            btn = tk.Button(preset_row,
                            text=p["name"],
                            bg=PRESET_BG, fg=ACCENT,
                            activebackground=ACCENT_H, activeforeground="#000",
                            relief="flat", cursor="hand2",
                            font=("Segoe UI", 10, "bold"),
                            padx=10, pady=7,
                            command=lambda idx=i: self._select_preset(idx))
            btn.pack(side="left", padx=(0, 8))
            self._preset_btns.append(btn)

        # —— separador —————————————————————————————————————————————————————————
        tk.Frame(card, bg=SEP_CLR, height=1).pack(fill="x", padx=16, pady=2)

        # —— link manual ———————————————————————————————————————————————————————
        tk.Label(card, text="LINK MANUAL", bg=BG_CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(10, 3))

        self._url_var   = tk.StringVar()
        self._url_entry = tk.Entry(card, textvariable=self._url_var,
                                   bg=BG_ENTRY, fg=TEXT, insertbackground=ACCENT,
                                   relief="flat", font=("Segoe UI", 11), bd=0)
        self._url_entry.pack(fill="x", padx=16, ipady=9)
        self._url_entry.bind("<Button-3>", self._paste_right_click)
        self._url_entry.bind("<FocusIn>",  lambda _: self._clear_preset_highlight())

        # —— separador —————————————————————————————————————————————————————————
        tk.Frame(card, bg=SEP_CLR, height=1).pack(fill="x", padx=16, pady=8)

        # —— dispositivos chromecast ————————————————————————————————————————————
        dev_hdr = tk.Frame(card, bg=BG_CARD)
        dev_hdr.pack(fill="x", padx=16, pady=(0, 6))
        tk.Label(dev_hdr, text="DISPOSITIVOS CHROMECAST", bg=BG_CARD, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        self._btn_refresh = tk.Button(dev_hdr, text="↻",
                                      bg=BG_CARD, fg=ACCENT,
                                      activebackground=BG_DARK, activeforeground=ACCENT,
                                      relief="flat", cursor="hand2",
                                      font=("Segoe UI", 16, "bold"),
                                      command=self._search_thread)
        self._btn_refresh.pack(side="right")

        # contenedor dinámico de checkboxes
        self._cast_frame = tk.Frame(card, bg=BG_CARD)
        self._cast_frame.pack(fill="x", padx=20, pady=(0, 14))

        self._no_cast_lbl = tk.Label(self._cast_frame,
                                     text="(presioná ↻ para buscar dispositivos)",
                                     bg=BG_CARD, fg=MUTED, font=("Segoe UI", 10))
        self._no_cast_lbl.pack(anchor="w")

        # ── botón transmitir ──────────────────────────────────────────────────
        self._btn_tx = tk.Button(self, text="▶   Transmitir",
                                 bg=ACCENT, fg="#ffffff",
                                 activebackground=ACCENT_H, activeforeground="#ffffff",
                                 font=("Segoe UI", 14, "bold"),
                                 relief="flat", cursor="hand2", height=2,
                                 command=self._transmit_thread)
        self._btn_tx.pack(fill="x", padx=18, pady=(8, 4))
        self._btn_tx.bind("<Enter>", lambda _: self._btn_tx.config(bg=ACCENT_H) if self._ready else None)
        self._btn_tx.bind("<Leave>", lambda _: self._btn_tx.config(bg=ACCENT)   if self._ready else None)

        # ── mini controles (solo visibles al transmitir) ──────────────────────
        ctrl = tk.Frame(self, bg=BG_DARK)
        ctrl.pack(fill="x", padx=18, pady=(0, 4))
        self._btn_live = tk.Button(ctrl, text="↺   Ir al vivo  (sin retraso)",
                                   bg="#2a2a2a", fg=ACCENT,
                                   activebackground="#333", activeforeground=ACCENT_H,
                                   relief="flat", font=("Segoe UI", 11, "bold"),
                                   cursor="hand2", pady=7,
                                   command=self._go_live)
        self._btn_live.pack(fill="x")
        self._ctrl_frame = ctrl
        self._set_controls_visible(False)   # ocultos hasta que se transmita

        # ── barra de estado ───────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Iniciando…")
        self._status_lbl = tk.Label(self, textvariable=self._status_var,
                                    bg=STATUS_BG, fg=WARN_CLR,
                                    font=("Segoe UI", 10), anchor="w", padx=16)
        self._status_lbl.pack(fill="x", side="bottom", ipady=6)

    # ══════════════════════════════════════════════════════════════════════════
    # CONTROL DE ESTADO
    # ══════════════════════════════════════════════════════════════════════════
    def _lock_controls(self):
        self.after(0, lambda: [
            self._btn_tx.config(state="disabled", bg=ACCENT_D, cursor="", fg="#888"),
            self._btn_refresh.config(state="disabled"),
            self._url_entry.config(state="disabled"),
            [b.config(state="disabled") for b in self._preset_btns],
        ])

    def _unlock_controls(self):
        self._ready = True
        self.after(0, lambda: [
            self._btn_tx.config(state="normal", bg=ACCENT, cursor="hand2", fg="#000"),
            self._btn_refresh.config(state="normal"),
            self._url_entry.config(state="normal"),
            [b.config(state="normal") for b in self._preset_btns],
        ])

    def _set_action_buttons(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        bg    = ACCENT  if enabled else ACCENT_D
        fg    = "#000"  if enabled else "#888"
        cur   = "hand2" if enabled else ""
        self.after(0, lambda: [
            self._btn_tx.config(state=state, bg=bg, fg=fg, cursor=cur),
            self._btn_refresh.config(state=state),
        ])

    def _set_btn_state(self, mode: str):
        """
        Ciclo del botón principal:
          idle      → ▶ Transmitir  (dorado)
          fetching  → ✕ Cancelar    (oscuro / rojo)
          streaming → ⬛ Detener     (rojo)
        """
        if mode == "idle":
            self.after(0, lambda: [
                self._btn_tx.config(
                    text="▶   Transmitir", state="normal",
                    bg=ACCENT, fg="#fff",
                    activebackground=ACCENT_H, activeforeground="#fff",
                    command=self._transmit_thread),
                self._btn_refresh.config(state="normal"),
                self._set_controls_visible(False),
            ])
        elif mode == "fetching":
            self.after(0, lambda: [
                self._btn_tx.config(
                    text="✕   Cancelar", state="normal",
                    bg="#2a2a2a", fg=ERR_CLR,
                    activebackground="#333", activeforeground=ERR_CLR,
                    command=self._cancel_transmit),
                self._btn_refresh.config(state="disabled"),
                self._set_controls_visible(False),
            ])
        elif mode == "streaming":
            self.after(0, lambda: [
                self._btn_tx.config(
                    text="⬛   Detener", state="normal",
                    bg=ERR_CLR, fg="#fff",
                    activebackground="#cc2222", activeforeground="#fff",
                    command=self._stop_streaming),
                self._btn_refresh.config(state="normal"),
                self._set_controls_visible(True),
            ])

    def _set_controls_visible(self, visible: bool):
        if visible:
            self._ctrl_frame.pack(fill="x", padx=18, pady=(0, 4),
                                  before=self._status_lbl)
        else:
            self._ctrl_frame.pack_forget()

    def _cancel_transmit(self):
        self._cancelled = True
        proc = self._ytdlp_proc
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        self._set_status("Transmisión cancelada.")
        self._set_btn_state("idle")

    def _stop_streaming(self):
        for proc in self._vlc_procs:
            try: proc.kill()
            except Exception: pass
        self._vlc_procs.clear()
        self._active_cast_names.clear()
        self._set_status("Transmisión detenida.")
        self._set_btn_state("idle")

    def _set_status(self, msg: str, *, err=False, warn=False):
        color = ERR_CLR if err else (WARN_CLR if warn else OK_CLR)
        self.after(0, lambda: [
            self._status_var.set(msg),
            self._status_lbl.config(fg=color),
        ])

    # ── helpers UI ────────────────────────────────────────────────────────────
    def _paste_right_click(self, _):
        try:
            self._url_var.set(self.clipboard_get())
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # PRESETS
    # ══════════════════════════════════════════════════════════════════════════
    def _select_preset(self, idx: int):
        url = self._presets[idx]["url"].strip()
        if not url:
            self._set_status(
                f"⚙  Configura la URL para «{self._presets[idx]['name']}» con el botón ⚙",
                warn=True)
            return
        self._url_var.set(url)
        self._selected_preset = idx
        self._set_status(f"Preset: {self._presets[idx]['name']}")
        self._refresh_preset_highlight()

    def _clear_preset_highlight(self):
        self._selected_preset = -1
        self._refresh_preset_highlight()

    def _refresh_preset_highlight(self):
        for i, btn in enumerate(self._preset_btns):
            if i == self._selected_preset:
                btn.config(bg=ACCENT, fg="#000")
            else:
                btn.config(bg=PRESET_BG, fg=ACCENT)

    def _open_preset_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Configurar Hipódromos")
        dlg.geometry("520x210")
        dlg.configure(bg=BG_DARK)
        dlg.resizable(False, False)
        dlg.grab_set()

        entry_cfg = dict(bg=BG_ENTRY, fg=TEXT, insertbackground=ACCENT,
                         relief="flat", font=("Segoe UI", 9), bd=4)

        url_vars: list[tk.StringVar] = []

        for p in self._presets:
            grp = tk.Frame(dlg, bg=BG_DARK)
            grp.pack(fill="x", padx=16, pady=(8, 0))
            tk.Label(grp, text=p["name"], bg=BG_DARK, fg=ACCENT,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w")

            r1 = tk.Frame(grp, bg=BG_DARK)
            r1.pack(fill="x", pady=(2, 0))
            tk.Label(r1, text="Stream:", bg=BG_DARK, fg=MUTED,
                     font=("Segoe UI", 8), width=8, anchor="w").pack(side="left")
            vu = tk.StringVar(value=p.get("url", ""))
            tk.Entry(r1, textvariable=vu, **entry_cfg).pack(side="left", fill="x", expand=True)
            url_vars.append(vu)

        def _save():
            for i in range(len(self._presets)):
                self._presets[i]["url"] = url_vars[i].get().strip()
            _save_presets(self._presets)
            self._update_hoy_strip()
            dlg.destroy()
            self._set_status("Presets guardados.")

        btn_row = tk.Frame(dlg, bg=BG_DARK)
        btn_row.pack(pady=14)
        tk.Button(btn_row, text="Cancelar",
                  bg=BG_CARD, fg=TEXT, activebackground=BG_ENTRY,
                  relief="flat", padx=14, pady=4,
                  command=dlg.destroy).pack(side="left", padx=6)
        tk.Button(btn_row, text="  Guardar  ",
                  bg=ACCENT, fg="#000", activebackground=ACCENT_H,
                  relief="flat", padx=14, pady=4, font=("Segoe UI", 9, "bold"),
                  command=_save).pack(side="left", padx=6)

    # ══════════════════════════════════════════════════════════════════════════
    # DISPOSITIVOS (checkboxes multi-select)
    # ══════════════════════════════════════════════════════════════════════════
    def _update_cast_checkboxes(self, names: list[str]):
        for w in self._cast_frame.winfo_children():
            w.destroy()
        self._cast_vars = {}

        if not names:
            tk.Label(self._cast_frame, text="(sin dispositivos en la red)",
                     bg=BG_CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            return

        for name in names:
            var = tk.BooleanVar(value=True)
            self._cast_vars[name] = var
            cb = tk.Checkbutton(self._cast_frame,
                                text=f"  {name}",
                                variable=var,
                                bg=BG_CARD, fg=TEXT,
                                selectcolor=BG_ENTRY,
                                activebackground=BG_CARD,
                                activeforeground=ACCENT,
                                font=("Segoe UI", 11),
                                anchor="w", cursor="hand2")
            cb.pack(fill="x", pady=2)

    # ══════════════════════════════════════════════════════════════════════════
    # IMÁGENES (logo + marca de agua)
    # ══════════════════════════════════════════════════════════════════════════
    def _apply_images(self):
        try:
            from PIL import Image, ImageTk, ImageDraw
            if not os.path.isfile(CAT_IMG):
                return
            cat = Image.open(CAT_IMG).convert("RGBA")
            w, h = cat.size

            # logo circular con anillo dorado
            LOGO, RING = 52, 4
            s    = min(w, h)
            left = (w - s) // 2
            top  = max(0, (h - s) // 2 - s // 10)
            crop = cat.crop((left, top, left + s, top + s)).resize((LOGO, LOGO), Image.LANCZOS)

            mask = Image.new("L", (LOGO, LOGO), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, LOGO - 1, LOGO - 1), fill=255)
            circle = Image.new("RGBA", (LOGO, LOGO), (0, 0, 0, 0))
            circle.paste(crop, mask=mask)

            total = LOGO + RING * 2
            canvas = Image.new("RGBA", (total, total), (0, 0, 0, 0))
            rm = Image.new("L", (total, total), 0)
            ImageDraw.Draw(rm).ellipse((0, 0, total - 1, total - 1), fill=255)
            canvas.paste(Image.new("RGBA", (total, total), (*RING_CLR, 255)), mask=rm)
            inner = LOGO + 2
            off   = (total - inner) // 2
            hm    = Image.new("L", (total, total), 0)
            ImageDraw.Draw(hm).ellipse((off, off, off + inner - 1, off + inner - 1), fill=255)
            canvas.paste(Image.new("RGBA", (total, total), (198, 212, 223, 255)), mask=hm)
            canvas.paste(circle, (RING + 1, RING + 1), circle)

            self._logo_photo = ImageTk.PhotoImage(canvas)
            self.after(0, lambda: self._logo_lbl.config(image=self._logo_photo))

            # ícono .ico para barra de tareas y título de ventana
            ico_path = os.path.join(APP_DIR, "pepistream.ico")
            base = canvas.convert("RGBA")
            sizes = [16, 32, 48, 64, 128]
            frames = [base.resize((s, s), Image.LANCZOS) for s in sizes]
            frames[0].save(ico_path, format="ICO",
                           sizes=[(s, s) for s in sizes],
                           append_images=frames[1:])
            self.after(0, lambda: self.iconbitmap(ico_path))

            # marca de agua
            WM = 190
            wm = cat.copy()
            wm.thumbnail((WM, int(WM * h / w)), Image.LANCZOS)
            r, g, b, a = wm.split()
            wm.putalpha(a.point(lambda x: int(x * 0.13)))
            bg = Image.new("RGBA", wm.size, (15, 15, 15, 255))
            bg.paste(wm, (0, 0), wm)
            self._wm_photo = ImageTk.PhotoImage(bg.convert("RGB"))

            def _place():
                lbl = tk.Label(self, image=self._wm_photo, bg=BG_DARK, bd=0)
                lbl.place(relx=1.0, rely=1.0, anchor="se", x=-14, y=-38)
                lbl.lower()
            self.after(0, _place)

        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    # AUTO-SETUP
    # ══════════════════════════════════════════════════════════════════════════
    def _auto_setup(self):

        # Pillow
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self._set_status("Instalando Pillow…", warn=True)
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install",
                                       "pillow", "--quiet"], creationflags=NO_WINDOW)
                importlib.invalidate_caches()
            except Exception as exc:
                self._set_status(f"Error instalando Pillow: {exc}", err=True)
        self._apply_images()

        # requests + beautifulsoup4 (para scraping del calendario)
        for pkg, imp in [("requests", "requests"), ("beautifulsoup4", "bs4")]:
            try:
                importlib.import_module(imp)
            except ImportError:
                self._set_status(f"Instalando {pkg}…", warn=True)
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install",
                                           pkg, "--quiet"], creationflags=NO_WINDOW)
                    importlib.invalidate_caches()
                except Exception:
                    pass

        # pychromecast
        try:
            import pychromecast  # noqa: F401
        except ImportError:
            self._set_status("Instalando pychromecast (primera vez)…", warn=True)
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install",
                                       "pychromecast", "--quiet"], creationflags=NO_WINDOW)
                importlib.invalidate_caches()
                import pychromecast  # noqa: F401
            except Exception as exc:
                self._set_status(f"Error instalando pychromecast: {exc}", err=True)
                return

        # yt-dlp
        if not shutil.which("yt-dlp"):
            if os.path.isfile(YTDLP_LOCAL):
                _prepend_path(APP_DIR)
            else:
                self._set_status("Descargando yt-dlp (primera vez)…", warn=True)
                try:
                    def _prog(count, block, total):
                        if total > 0:
                            self._set_status(
                                f"Descargando yt-dlp… {min(int(count*block*100/total),100)}%",
                                warn=True)
                    urllib.request.urlretrieve(YTDLP_URL, YTDLP_LOCAL, _prog)
                    _prepend_path(APP_DIR)
                except Exception as exc:
                    self._set_status(f"Error descargando yt-dlp: {exc}", err=True)
                    return

        self._unlock_controls()
        self._update_hoy_strip()   # muestra desde caché si existe
        threading.Thread(target=self._fetch_today_info, daemon=True).start()
        self._set_status("Buscando dispositivos Chromecast…")
        self._search_thread()

    # ══════════════════════════════════════════════════════════════════════════
    # BÚSQUEDA DE CHROMECASTS
    # ══════════════════════════════════════════════════════════════════════════
    def _search_thread(self):
        threading.Thread(target=self._search, daemon=True).start()

    def _search(self):
        self._set_action_buttons(False)
        self._set_status("Buscando dispositivos Chromecast en la red…")
        try:
            import pychromecast

            self._casts.clear()

            # Solo discovery mDNS — no creamos objetos Chromecast, solo necesitamos IPs
            from pychromecast.discovery import discover_chromecasts, stop_discovery
            services, browser = discover_chromecasts(timeout=8)
            stop_discovery(browser)

            for svc in services:
                self._casts[svc.friendly_name] = svc.host

            names = list(self._casts)
            self.after(0, lambda: self._update_cast_checkboxes(names))

            if names:
                p = "s" if len(names) > 1 else ""
                self._set_status(f"✓  {len(names)} dispositivo{p} encontrado{p}  —  selecciona los que quieras")
            else:
                self._set_status("No se encontraron Chromecasts en la red local", err=True)

        except Exception as exc:
            self._set_status(f"Error al buscar dispositivos: {exc}", err=True)
        finally:
            self._set_action_buttons(True)

    # ══════════════════════════════════════════════════════════════════════════
    # TRANSMISIÓN (multi-Chromecast)
    # ══════════════════════════════════════════════════════════════════════════
    def _transmit_thread(self):
        threading.Thread(target=self._transmit, daemon=True).start()

    def _transmit(self):
        url = self._url_var.get().strip()
        if not url:
            self._set_status("⚠  Selecciona un hipódromo o pega un link", err=True)
            return

        selected = [(n, ip) for n, ip in self._casts.items()
                    if n in self._cast_vars and self._cast_vars[n].get()]
        if not selected:
            self._set_status("⚠  Selecciona al menos un dispositivo Chromecast", err=True)
            return

        self._cancelled = False
        self._set_btn_state("fetching")

        # ── extraer URL del stream ─────────────────────────────────────────
        self._set_status("Extrayendo URL de stream…  (✕ Cancelar para abortar)")
        stream_url = None
        try:
            self._ytdlp_proc = subprocess.Popen(
                ["yt-dlp", "-g",
                 "-f", "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio/best",
                 "--no-playlist", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=NO_WINDOW,
            )
            try:
                stdout, stderr = self._ytdlp_proc.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                self._ytdlp_proc.kill()
                self._ytdlp_proc.wait()
                self._ytdlp_proc = None
                if not self._cancelled:
                    self._set_status("⚠  Sin respuesta — el canal probablemente no está en vivo", err=True)
                    self._set_btn_state("idle")
                return

            rc = self._ytdlp_proc.returncode
            self._ytdlp_proc = None

            if self._cancelled:
                return

            if rc != 0:
                last = (stderr.decode(errors="replace").strip().splitlines()
                        or ["Error desconocido"])[-1]
                raise RuntimeError(last)

            lines = [l.strip() for l in stdout.decode(errors="replace").strip().splitlines()
                     if l.strip().startswith("http")]
            if not lines:
                raise RuntimeError("yt-dlp no devolvió ninguna URL — ¿el canal está en vivo?")
            stream_url = lines[0]

        except FileNotFoundError:
            self._set_status("⚠  yt-dlp no encontrado — reinicia la app", err=True)
            self._set_btn_state("idle")
            return
        except Exception as exc:
            if not self._cancelled:
                self._set_status(f"Error: {exc}", err=True)
            self._set_btn_state("idle")
            return

        # ── lanzar VLC (invisible) por cada Chromecast ───────────────────
        if not os.path.isfile(VLC_PATH):
            self._set_status(f"⚠  VLC no encontrado en {VLC_PATH}", err=True)
            self._set_btn_state("idle")
            return

        for proc in self._vlc_procs:
            try: proc.kill()
            except Exception: pass
        self._vlc_procs.clear()
        self._active_cast_names.clear()
        self._current_url = url

        launched, failed = [], []
        for name, ip in selected:
            self._set_status(f"Conectando a «{name}»…")
            try:
                proc = subprocess.Popen(
                    [VLC_PATH, stream_url,
                     "--intf", "dummy", "--dummy-quiet",
                     f"--sout=#chromecast{{ip={ip},mux=mp4}}",
                     "--sout-keep", "--no-video-title-show"],
                    startupinfo=_hidden_si(),
                )
                self._vlc_procs.append(proc)
                self._active_cast_names.append(name)
                launched.append(name)
            except Exception as exc:
                failed.append(f"{name}: {exc}")

        if launched and not failed:
            self._set_status(f"✓  Transmitiendo a: {'  |  '.join(launched)}")
            self._set_btn_state("streaming")
        elif launched and failed:
            self._set_status(f"✓ {len(launched)} OK  /  ⚠ {failed[0]}", warn=True)
            self._set_btn_state("streaming")
        else:
            # mostrar el error real para poder diagnosticar
            self._set_status(f"Error: {failed[0] if failed else 'sin dispositivos'}", err=True)
            self._set_btn_state("idle")


    # ══════════════════════════════════════════════════════════════════════════
    # CONTROLES DE REPRODUCCIÓN
    # ══════════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════════
    # CALENDARIO
    # ══════════════════════════════════════════════════════════════════════════
    def _update_hoy_strip(self):
        """Muestra hipódromo de hoy desde caché de turfpremium o calendario manual."""
        from datetime import date
        today = date.today()
        # 1. caché de turfpremium (prioritario)
        hipo = ""
        cache = _load_race_cache()
        if cache:
            hipo = cache.get("races", {}).get(today.isoformat(), "")
        # 2. calendario manual como fallback
        if not hipo:
            hipo = self._calendar.get(str(today.weekday()), "")

        if hipo:
            self.after(0, lambda h=hipo: self._hoy_lbl.config(text=h, fg=TEXT))
            self.after(0, lambda h=hipo: self._select_by_name(h))
        else:
            self.after(0, lambda: self._hoy_lbl.config(text="Sin datos", fg=MUTED))

    def _fetch_today_info(self):
        """Busca en turfpremium el hipódromo de hoy y los horarios. Corre en background."""
        import requests, re
        from bs4 import BeautifulSoup
        from datetime import date

        try:
            today = date.today()
            s = requests.Session()
            s.headers["User-Agent"] = SCRAPE_UA
            s.get(TURFPREMIUM_LOGIN, timeout=10)

            # ── hipódromo de hoy ──────────────────────────────────────────────
            r    = s.get(TURFPREMIUM_PROGRA, timeout=15)
            r.encoding = r.apparent_encoding or "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")

            hipo = ""
            for a in soup.find_all("a", class_="menuprogint"):
                href = a.get("href", "")
                m    = re.search(r"idfec=(\d{4})/(\d{1,2})/(\d{1,2})", href)
                if m:
                    try:
                        if date(int(m.group(1)), int(m.group(2)), int(m.group(3))) == today:
                            parts = a.get_text(" ", strip=True).split()
                            abbr = parts[-1].strip() if parts else ""
                            hipo = TURFPREMIUM_MAP.get(abbr, "")
                            break
                    except ValueError:
                        pass

            if hipo:
                self.after(0, lambda h=hipo: self._hoy_lbl.config(text=h, fg=TEXT))
                self.after(0, lambda h=hipo: self._select_by_name(h))

            # ── horarios: primera y última carrera ────────────────────────────
            fecha = f"{today.year}/{today.month:02d}/{today.day:02d}"
            r2    = s.get(
                f"https://turfpremium.com.ar/web/web/gral/progra/"
                f"progranrocarr.php?idfec={fecha}&idi=es",
                timeout=15)
            r2.encoding = r2.apparent_encoding or "utf-8"
            soup2 = BeautifulSoup(r2.text, "html.parser")

            times = [b.get_text(strip=True)
                     for b in soup2.find_all("b")
                     if re.match(r'^\d{1,2}:\d{2}$', b.get_text(strip=True))]
            if times:
                txt = f"{times[0]} — {times[-1]} hs"
                self.after(0, lambda t=txt: self._hoy_hours_lbl.config(text=t))

        except Exception:
            pass

    def _open_programa_thread(self):
        threading.Thread(target=self._open_programa, daemon=True).start()

    def _open_programa(self):
        import requests
        from bs4 import BeautifulSoup
        from datetime import date

        self._set_status("Buscando programa del día…", warn=True)
        try:
            today = date.today()
            fecha = f"{today.year}/{today.month:02d}/{today.day:02d}"
            url   = (f"https://turfpremium.com.ar/web/web/gral/progra/"
                     f"progranrocarr.php?idfec={fecha}&idi=es")

            s = requests.Session()
            s.headers["User-Agent"] = SCRAPE_UA
            s.get(TURFPREMIUM_LOGIN, timeout=10)
            r = s.get(url, timeout=15)
            r.encoding = r.apparent_encoding or "utf-8"
            soup = BeautifulSoup(r.text, "html.parser")

            a = soup.find("a", class_="pdf")
            if a and a.get("href"):
                pdf_url = a["href"].strip()
                self._set_status(f"Abriendo programa: {pdf_url.split('/')[-1]}")
                webbrowser.open(pdf_url)
                return

            # ── fallback según hipódromo ─────────────────────────────────────
            cache    = _load_race_cache()
            hoy_hipo = cache.get("races", {}).get(today.isoformat(), "") if cache else ""

            if "palermo" in hoy_hipo.lower():
                self._set_status("Buscando en palermo.com.ar…", warn=True)
                pdf_url = _palermo_programa_pdf(today)
            elif "isidro" in hoy_hipo.lower():
                self._set_status("Buscando en hipodromosanisidro.com…", warn=True)
                pdf_url = _san_isidro_programa_pdf(today)
            else:
                pdf_url = ""

            if pdf_url:
                self._set_status(f"Abriendo programa: {pdf_url.split('/')[-1]}")
                webbrowser.open(pdf_url)
                return

            self._set_status("⚠  No se encontró el PDF del programa de hoy", err=True)
        except Exception as exc:
            self._set_status(f"Error buscando programa: {exc}", err=True)

    def _open_hoy_website(self):
        from datetime import date
        idx  = str(date.today().weekday())
        hipo = self._calendar.get(idx, "")
        web  = _preset_website(hipo)
        if web:
            webbrowser.open(web)

    def _open_calendar_dialog(self):
        from datetime import date
        today_idx = date.today().weekday()

        dlg = tk.Toplevel(self)
        dlg.title("Calendario semanal")
        dlg.geometry("400x310")
        dlg.configure(bg=BG_DARK)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Asigná un hipódromo a cada día",
                 bg=BG_DARK, fg=MUTED, font=("Segoe UI", 8)).pack(pady=(12, 8))

        opciones = ["(ninguno)"] + [p["name"] for p in self._presets]
        vars_list = []

        for i, day in enumerate(DIAS_ES):
            row = tk.Frame(dlg, bg=BG_DARK)
            row.pack(fill="x", padx=18, pady=3)

            fg = ACCENT if i == today_idx else TEXT
            weight = "bold" if i == today_idx else "normal"
            tk.Label(row, text=("▶ " if i == today_idx else "   ") + day,
                     bg=BG_DARK, fg=fg,
                     font=("Segoe UI", 9, weight),
                     width=14, anchor="w").pack(side="left")

            current = self._calendar.get(str(i), "")
            var = tk.StringVar(value=current if current else "(ninguno)")
            combo = ttk.Combobox(row, textvariable=var, values=opciones,
                                 state="readonly", style="P.TCombobox",
                                 font=("Segoe UI", 9), width=22)
            combo.pack(side="left")

            # botón que abre el sitio web del hipódromo seleccionado
            def _make_web_cmd(v=var):
                def _cmd():
                    web = _preset_website(v.get())
                    if web: webbrowser.open(web)
                return _cmd
            tk.Button(row, text="🌐", bg=BG_DARK, fg=MUTED,
                      activebackground=BG_DARK, activeforeground=ACCENT,
                      relief="flat", cursor="hand2", font=("Segoe UI", 10),
                      command=_make_web_cmd()).pack(side="left", padx=(4, 0))

            vars_list.append((str(i), var))

        def _save():
            for day_idx, var in vars_list:
                val = var.get()
                self._calendar[day_idx] = "" if val == "(ninguno)" else val
            _save_calendar(self._calendar)
            self._update_hoy_strip()
            dlg.destroy()

        btn_row = tk.Frame(dlg, bg=BG_DARK)
        btn_row.pack(pady=14)
        tk.Button(btn_row, text="Cancelar", bg=BG_CARD, fg=TEXT,
                  activebackground=BG_ENTRY, relief="flat", padx=12, pady=4,
                  command=dlg.destroy).pack(side="left", padx=6)
        tk.Button(btn_row, text="  Guardar  ", bg=ACCENT, fg="#000",
                  activebackground=ACCENT_H, relief="flat", padx=12, pady=4,
                  font=("Segoe UI", 9, "bold"), command=_save).pack(side="left", padx=6)

    def _select_by_name(self, name: str):
        for i, p in enumerate(self._presets):
            if p["name"] == name:
                self._select_preset(i)
                return

    def _open_month_calendar(self):
        CalendarDialog(self)

    def _go_live(self):
        if not self._current_url:
            return
        for proc in self._vlc_procs:
            try: proc.kill()
            except Exception: pass
        self._vlc_procs.clear()
        self._url_var.set(self._current_url)
        self._transmit_thread()


# ── utilidades ────────────────────────────────────────────────────────────────
def _hidden_si() -> subprocess.STARTUPINFO:
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si


def _prepend_path(directory: str):
    os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")


class CalendarDialog(tk.Toplevel):
    """Calendario mensual con datos scrapeados de las webs oficiales."""
    CELL_W, CELL_H = 74, 58

    def __init__(self, app):
        super().__init__(app)
        self._app   = app
        from datetime import date
        _t = date.today()
        self._year, self._month = _t.year, _t.month
        self._races:       dict = {}
        self._frames:      list = []
        self._pending_day: str  = ""

        self.title("Calendario de carreras")
        self.geometry("580x580")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.grab_set()

        self._build()
        self._load_data()

    # ── construcción ─────────────────────────────────────────────────────────
    def _build(self):
        # encabezado
        hdr = tk.Frame(self, bg=BG_DARK)
        hdr.pack(fill="x", padx=14, pady=(12, 4))
        tk.Button(hdr, text="◄", bg=BG_DARK, fg=TEXT,
                  activebackground=BG_CARD, relief="flat",
                  font=("Segoe UI", 14), cursor="hand2",
                  command=lambda: self._shift(-1)).pack(side="left")
        self._hdr_var = tk.StringVar()
        tk.Label(hdr, textvariable=self._hdr_var, bg=BG_DARK, fg=TEXT,
                 font=("Segoe UI", 15, "bold"), width=20).pack(side="left")
        tk.Button(hdr, text="►", bg=BG_DARK, fg=TEXT,
                  activebackground=BG_CARD, relief="flat",
                  font=("Segoe UI", 14), cursor="hand2",
                  command=lambda: self._shift(1)).pack(side="left")
        self._btn_ref = tk.Button(hdr, text="↻  Actualizar",
                                   bg=BG_CARD, fg=ACCENT,
                                   activebackground=BG_ENTRY, relief="flat",
                                   cursor="hand2", font=("Segoe UI", 10),
                                   padx=8, pady=4,
                                   command=self._force_refresh)
        self._btn_ref.pack(side="right")
        self._update_hdr()

        # grilla
        grid = tk.Frame(self, bg=BG_DARK)
        grid.pack(padx=10, pady=6)
        for col, d in enumerate(DIAS_SHORT):
            tk.Label(grid, text=d, bg=BG_DARK, fg=MUTED,
                     font=("Segoe UI", 10, "bold"),
                     width=9).grid(row=0, column=col, pady=(0, 4))
        self._frames = []
        for row in range(6):
            rf = []
            for col in range(7):
                f = tk.Frame(grid, bg=BG_CARD,
                             width=self.CELL_W, height=self.CELL_H,
                             highlightthickness=1, highlightbackground=SEP_CLR)
                f.grid(row=row+1, column=col, padx=2, pady=2)
                f.pack_propagate(False)
                rf.append(f)
            self._frames.append(rf)

        # leyenda
        leg = tk.Frame(self, bg=BG_DARK)
        leg.pack(pady=(6, 0))
        for name, color in HIPO_COLORS.items():
            tk.Label(leg, text="●", bg=BG_DARK, fg=color,
                     font=("Segoe UI", 13)).pack(side="left", padx=(12, 3))
            tk.Label(leg, text=HIPO_ABBREV.get(name, name),
                     bg=BG_DARK, fg=TEXT,
                     font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))

        # barra de edición inline (oculta hasta que se haga clic en un día)
        self._sel_bar = tk.Frame(self, bg=BG_CARD, pady=6)
        self._sel_day_lbl = tk.Label(self._sel_bar, text="", bg=BG_CARD, fg=MUTED,
                                     font=("Segoe UI", 9, "bold"))
        self._sel_day_lbl.pack(side="left", padx=(12, 8))
        for _n in list(HIPO_COLORS.keys()):
            _c = HIPO_COLORS[_n]
            _ab = HIPO_ABBREV[_n]
            tk.Button(self._sel_bar, text=_ab,
                      bg=BG_DARK, fg=_c, activebackground=BG_ENTRY,
                      font=("Segoe UI", 9, "bold"), relief="flat",
                      padx=8, pady=3, cursor="hand2",
                      command=lambda n=_n: self._apply_day_event(n)).pack(side="left", padx=2)
        tk.Button(self._sel_bar, text="ninguno",
                  bg=BG_DARK, fg=MUTED, activebackground=BG_ENTRY,
                  font=("Segoe UI", 9), relief="flat",
                  padx=8, pady=3, cursor="hand2",
                  command=lambda: self._apply_day_event("")).pack(side="left", padx=(2, 12))

        # estado
        self._status_var = tk.StringVar(value="")
        self._status_lbl_w = tk.Label(self, textvariable=self._status_var,
                                      bg=BG_DARK, fg=MUTED, font=("Segoe UI", 9))
        self._status_lbl_w.pack(pady=(6, 10))

    # ── datos ─────────────────────────────────────────────────────────────────
    def _load_data(self):
        cache = _load_race_cache()
        if cache:
            self._races = cache.get("races", {})
            self._render()
            ts = cache.get("fetched_at", "")[:16].replace("T", " ")
            self._status_var.set(f"Actualizado: {ts}  —  clic en un día para editar el evento")
        else:
            self._force_refresh()

    def _force_refresh(self):
        self._status_var.set("Consultando webs oficiales…")
        self._btn_ref.config(state="disabled")
        threading.Thread(target=self._do_fetch, daemon=True).start()

    def _do_fetch(self):
        races = _fetch_race_calendar()
        from datetime import datetime
        # Merge: los datos manuales se preservan; la web solo sobreescribe los días que encuentra
        merged = dict(self._races)
        merged.update(races)
        cache = {"fetched_at": datetime.now().isoformat(), "races": merged}
        _save_race_cache(cache)
        self._races = merged
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.after(0, self._render)
        self.after(0, lambda: self._status_var.set(
            f"Actualizado: {now}  —  clic en un día para editar el evento"))
        self.after(0, lambda: self._btn_ref.config(state="normal"))

    # ── edición inline de evento por día ─────────────────────────────────────
    def _on_day_click(self, d_str: str):
        from datetime import date
        self._pending_day = d_str
        d = date.fromisoformat(d_str)
        self._sel_day_lbl.config(text=f"{d.day} {MESES_ES[d.month-1]}:")
        if not self._sel_bar.winfo_ismapped():
            self._sel_bar.pack(fill="x", pady=(6, 0), before=self._status_lbl_w)

    def _apply_day_event(self, hipo_name: str):
        d_str = self._pending_day
        if hipo_name:
            self._races[d_str] = hipo_name
        else:
            self._races.pop(d_str, None)
        from datetime import datetime
        cache = _load_race_cache() or {"fetched_at": datetime.now().isoformat(), "races": {}}
        cache["races"] = self._races
        _save_race_cache(cache)
        self._app._update_hoy_strip()
        self._sel_bar.pack_forget()
        self._render()

    # ── renderizado ───────────────────────────────────────────────────────────
    def _update_hdr(self):
        self._hdr_var.set(f"{MESES_ES[self._month-1].capitalize()}  {self._year}")

    def _shift(self, delta: int):
        self._month += delta
        if self._month > 12: self._month = 1;  self._year += 1
        if self._month < 1:  self._month = 12; self._year -= 1
        self._update_hdr()
        self._render()

    def _render(self):
        import calendar
        from datetime import date
        today = date.today()
        weeks = calendar.monthcalendar(self._year, self._month)
        while len(weeks) < 6:
            weeks.append([0] * 7)

        for row, week in enumerate(weeks):
            for col, day in enumerate(week):
                frame = self._frames[row][col]
                for w in frame.winfo_children():
                    w.destroy()
                frame.unbind("<Button-1>")

                if day == 0:
                    frame.config(bg="#0e0e0e", highlightbackground="#0e0e0e", cursor="")
                    continue

                d_str   = f"{self._year:04d}-{self._month:02d}-{day:02d}"
                # scraped data primero, manual como fallback
                hipo = self._races.get(d_str, "")
                if not hipo:
                    weekday = str(date(self._year, self._month, day).weekday())
                    hipo = self._app._calendar.get(weekday, "")

                is_today = (today == date(self._year, self._month, day))
                bg = "#222218" if is_today else (BG_CARD if hipo else "#161b22")
                frame.config(bg=bg,
                             highlightbackground=ACCENT if is_today else SEP_CLR,
                             cursor="hand2")

                num = tk.Label(frame, text=str(day), bg=bg,
                               fg=ACCENT if is_today else (TEXT if hipo else MUTED),
                               font=("Segoe UI", 12,
                                     "bold" if is_today else "normal"))
                num.pack(pady=(5, 0))

                widgets = [frame, num]
                if hipo:
                    color = HIPO_COLORS.get(hipo, TEXT)
                    ab    = HIPO_ABBREV.get(hipo, hipo[:8])
                    hi = tk.Label(frame, text=ab, bg=bg, fg=color,
                                  font=("Segoe UI", 8, "bold"))
                    hi.pack()
                    widgets.append(hi)

                for ww in widgets:
                    ww.bind("<Button-1>", lambda e, d=d_str: self._on_day_click(d))


def _hover(btn: tk.Button, fg_normal, fg_hover, bg_normal, bg_hover):
    btn.bind("<Enter>", lambda _: btn.config(fg=fg_hover, bg=bg_hover))
    btn.bind("<Leave>", lambda _: btn.config(fg=fg_normal, bg=bg_normal))


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
