"use strict";

// Canales de YouTube de los hipódromos que transmiten en vivo (clave: nombre en studbook).
const CANALES = {
  "Palermo":    { id: "UCsPzTlRn9qGmD35YgSi87ng", url: "https://www.youtube.com/@hipodromodepalermoshows9483/live" },
  "San Isidro": { id: "UC3M7efaO9uxT0LTl3BSKvGg", url: "https://www.youtube.com/@hipodromosanisidro/live" },
  "La Plata":   { id: "UCTcg_c_MwfrsKlZREklF2_w", url: "https://www.youtube.com/@hipodromodelaplataTV/live" },
};

const TZ = "America/Argentina/Buenos_Aires";
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
               "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const DIAS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

const app = document.getElementById("app");
let calendario = null;
const reuniones = {};

// Todo lo que viene de studbook pasa por acá antes de ir al DOM.
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const color = (c) => /^(#[0-9a-f]{3,6}|[a-z]+)$/i.test(c ?? "") ? c : "currentColor";

const ahoraAR = () => {
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23",
  }).formatToParts(new Date()).map((x) => [x.type, x.value]));
  return { fecha: `${p.year}-${p.month}-${p.day}`, hora: `${p.hour}:${p.minute}` };
};

const fechaLarga = (iso) => {
  const d = new Date(iso + "T12:00:00");
  return `${DIAS[d.getDay()]} ${d.getDate()} de ${MESES[d.getMonth()]}`;
};

async function getJSON(url) {
  const r = await fetch(url, { cache: "no-cache" });
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

async function cargarCalendario() {
  calendario = await getJSON("data/calendario.json");
  const act = new Date(calendario.actualizado);
  document.getElementById("actualizado").textContent =
    "actualizado " + act.toLocaleString("es-AR", { timeZone: TZ, dateStyle: "short", timeStyle: "short" });
}

async function cargarReunion(id) {
  return (reuniones[id] ??= getJSON(`data/reuniones/${id}.json`));
}

// ── Piezas ──────────────────────────────────────────────────────────────────

const chip = (r) =>
  `<span class="chip" style="--c:${color(r.color)}">${esc(r.sigla)}</span>`;

const mandil = (p) =>
  `<span class="mandil" style="background:${color(p.mandil)};color:${color(p.mandil_texto)}">${esc(p.numero)}</span>`;

const vivo = (r) => {
  const c = CANALES[r.hipodromo];
  if (!c) return `<p class="aviso">${esc(r.hipodromo)} no tiene transmisión en YouTube.</p>`;
  return `
    <div class="video">
      <iframe src="https://www.youtube.com/embed/live_stream?channel=${c.id}&autoplay=1&mute=1"
        title="Vivo ${esc(r.hipodromo)}" allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
        allowfullscreen loading="lazy"></iframe>
    </div>
    <p class="links-vivo"><a href="${c.url}" target="_blank" rel="noopener">Abrir en YouTube ↗</a>
      <span class="sutil">si no carga acá o para castear desde el celular</span></p>`;
};

function participante(p, resultados) {
  const detalle = [p.jockey && `J: ${esc(p.jockey)}`, p.kg && `${esc(p.kg)} kg`,
                   p.entrenador && `E: ${esc(p.entrenador)}`].filter(Boolean).join(" · ");
  const extra = resultados
    ? `<span class="puesto">${esc(p.puesto)}º</span><span class="sutil">${esc(p.cuerpos ?? "")}</span>${p.pago ? `<span class="pago">$${esc(p.pago)}</span>` : ""}`
    : `<span class="ultimas" title="Últimas actuaciones">${esc(p.ultimas ?? "")}</span>`;
  return `
    <li class="corredor">
      ${mandil(p)}
      <div class="cuerpo">
        <strong>${esc(p.nombre)}</strong>
        ${p.padres ? `<span class="sutil">${esc(p.padres)}</span>` : ""}
        <span class="detalle">${detalle}</span>
        ${p.caballeriza ? `<span class="sutil">${esc(p.caballeriza)}</span>` : ""}
      </div>
      <div class="extra">${extra}</div>
    </li>`;
}

function carrera(c, abierta, proxima, rid) {
  const datos = [c.distancia && `${c.distancia} m`, c.pista, c.categoria].filter(Boolean).map(esc).join(" · ");
  const ganador = c.resultados && c.participantes.find((p) => p.puesto === "1");
  const video = c.video && /^https:\/\/www\.youtube\.com\/embed\/[\w-]+$/.test(c.video)
    ? c.video.replace("/embed/", "/watch?v=") : null;
  return `
    <details class="carrera${proxima ? " proxima" : ""}" id="r${rid}-c${c.numero}" ${abierta ? "open" : ""}>
      <summary>
        <span class="num">${c.numero}ª</span>
        <span class="hora">${esc(c.hora ?? "")}</span>
        <span class="titulo">${esc(c.premio ?? "")}<span class="sutil">${datos}</span></span>
        ${proxima ? `<span class="badge">Próxima</span>` : ""}
        ${ganador ? `<span class="ganador">🏆 ${esc(ganador.nombre)}</span>` : ""}
      </summary>
      ${c.condicion ? `<p class="condicion">${esc(c.condicion)}</p>` : ""}
      <p class="sutil">${c.bolsa ? `Bolsa ${esc(c.bolsa)}` : ""} ${video ? `· <a href="${video}" target="_blank" rel="noopener">Ver la carrera ↗</a>` : ""}</p>
      <ol class="corredores">${c.participantes.map((p) => participante(p, c.resultados)).join("")}</ol>
    </details>`;
}

function programa(d, esHoy) {
  const ahora = ahoraAR().hora;
  // "Próxima" = primera carrera sin resultados cuyo horario no pasó hace más de 10 min.
  const proxima = esHoy ? d.carreras_detalle.find((c) => !c.resultados && (!c.hora || c.hora >= restarMin(ahora, 10))) : null;
  return `
    <div class="acciones">
      ${d.pdf ? `<a class="boton" href="${esc(d.pdf)}" target="_blank" rel="noopener">Programa PDF ↗</a>` : ""}
      <a class="boton secundario" href="${esc(d.url)}" target="_blank" rel="noopener">Ver en studbook ↗</a>
    </div>
    <nav class="saltos">${d.carreras_detalle.map((c) => `<a href="#r${d.id}-c${c.numero}" data-salto>${c.numero}ª</a>`).join("")}</nav>
    ${d.carreras_detalle.map((c) => carrera(c, c === proxima, c === proxima, d.id)).join("")}`;
}

const restarMin = (hhmm, min) => {
  const [h, m] = hhmm.split(":").map(Number);
  const t = Math.max(0, h * 60 + m - min);
  return `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`;
};

function encabezado(r) {
  return `<h2 class="reunion-titulo">${chip(r)} ${esc(r.hipodromo)}
    <span class="sutil">${fechaLarga(r.fecha)} · ${r.carreras ?? "?"} carreras</span></h2>`;
}

async function bloqueReunion(r, { conVivo, esHoy }) {
  if (!r.programa) {
    return `<section class="reunion">${encabezado(r)}${conVivo ? vivo(r) : ""}
      <p class="aviso">Sin programa cargado. <a href="${esc(r.url)}" target="_blank" rel="noopener">Ver en studbook ↗</a></p></section>`;
  }
  const d = await cargarReunion(r.id);
  return `<section class="reunion">${encabezado(r)}${conVivo ? vivo(r) : ""}${programa(d, esHoy)}</section>`;
}

// ── Vistas ──────────────────────────────────────────────────────────────────

async function vistaHoy() {
  const hoy = ahoraAR().fecha;
  const deHoy = calendario.reuniones.filter((r) => r.fecha === hoy);
  if (deHoy.length) {
    const bloques = await Promise.all(deHoy.map((r) => bloqueReunion(r, { conVivo: true, esHoy: true })));
    return `<h1>Hoy, ${fechaLarga(hoy)}</h1>${bloques.join("")}`;
  }
  const proximas = calendario.reuniones.filter((r) => r.fecha > hoy);
  if (!proximas.length) return `<h1>Hoy no hay carreras</h1><p class="aviso">Y no hay reuniones próximas cargadas.</p>`;
  const fecha = proximas[0].fecha;
  const bloques = await Promise.all(proximas.filter((r) => r.fecha === fecha)
    .map((r) => bloqueReunion(r, { conVivo: false, esHoy: false })));
  return `<h1>Hoy no hay carreras</h1><p class="sutil">Próxima reunión: ${fechaLarga(fecha)}</p>${bloques.join("")}`;
}

async function vistaReunion(id) {
  const r = calendario.reuniones.find((x) => x.id === id);
  if (!r) return `<p class="aviso">No encontré esa reunión.</p>`;
  const esHoy = r.fecha === ahoraAR().fecha;
  return `<p><a href="#/calendario/${r.fecha.slice(0, 7)}">← Calendario</a></p>` +
    await bloqueReunion(r, { conVivo: esHoy, esHoy });
}

function vistaCalendario(mes) {
  const hoy = ahoraAR().fecha;
  const disponibles = [...new Set(calendario.reuniones.map((r) => r.fecha.slice(0, 7)))].sort();
  if (!disponibles.includes(hoy.slice(0, 7))) disponibles.push(hoy.slice(0, 7));
  disponibles.sort();
  mes = disponibles.includes(mes) ? mes : hoy.slice(0, 7);
  const i = disponibles.indexOf(mes);
  const [anio, m] = mes.split("-").map(Number);

  const porDia = {};
  for (const r of calendario.reuniones) if (r.fecha.startsWith(mes)) (porDia[r.fecha] ??= []).push(r);

  const primero = new Date(anio, m - 1, 1).getDay();
  const diasMes = new Date(anio, m, 0).getDate();
  let celdas = "";
  for (let k = 0; k < primero; k++) celdas += `<div class="dia vacio" aria-hidden="true"></div>`;
  for (let d = 1; d <= diasMes; d++) {
    const iso = `${mes}-${String(d).padStart(2, "0")}`;
    const rs = porDia[iso] ?? [];
    const links = rs.map((r) => {
      const href = r.programa ? `#/reunion/${r.id}` : esc(r.url);
      const ext = r.programa ? "" : ` target="_blank" rel="noopener"`;
      return `<a class="evento" href="${href}"${ext} style="--c:${color(r.color)}" title="${esc(r.hipodromo)}: ${r.carreras ?? "?"} carreras">
        <span class="sigla">${esc(r.sigla)}</span><span class="nombre">${esc(r.hipodromo)}</span></a>`;
    }).join("");
    const clase = ["dia", iso === hoy && "hoy", iso < hoy && "pasado"].filter(Boolean).join(" ");
    celdas += `<div class="${clase}"><span class="n">${d}</span>${links}</div>`;
  }

  const hipodromos = new Map(calendario.reuniones.filter((r) => r.fecha.startsWith(mes)).map((r) => [r.hipodromo, r]));
  return `
    <div class="cal-cabecera">
      ${i > 0 ? `<a class="boton secundario" href="#/calendario/${disponibles[i - 1]}" aria-label="Mes anterior">‹</a>` : `<span></span>`}
      <h1>${MESES[m - 1]} ${anio}</h1>
      ${i < disponibles.length - 1 ? `<a class="boton secundario" href="#/calendario/${disponibles[i + 1]}" aria-label="Mes siguiente">›</a>` : `<span></span>`}
    </div>
    <div class="cal">
      ${DIAS.map((d) => `<div class="cab">${d}</div>`).join("")}
      ${celdas}
    </div>
    <p class="leyenda">${[...hipodromos.values()].map((r) => `${chip(r)} ${esc(r.hipodromo)}`).join(" ")}</p>
    <p class="sutil">Los programas completos están disponibles para las reuniones de los últimos días y la próxima semana;
      el resto abre en studbook.</p>`;
}

// ── Router ──────────────────────────────────────────────────────────────────

async function render() {
  const [, ruta, arg] = location.hash.split("/");
  const tab = ruta === "calendario" || ruta === "reunion" ? "calendario" : "hoy";
  document.querySelectorAll("[data-tab]").forEach((a) =>
    a.toggleAttribute("aria-current", a.dataset.tab === tab));
  try {
    if (!calendario) await cargarCalendario();
    app.innerHTML = ruta === "calendario" ? vistaCalendario(arg)
      : ruta === "reunion" ? await vistaReunion(Number(arg))
      : await vistaHoy();
  } catch (e) {
    console.error(e);
    app.innerHTML = `<p class="aviso">No pude cargar los datos. Probá recargar en un rato.</p>`;
  }
}

// Los saltos a carrera (#r<reunión>-c<N>) no deben disparar el router: abren y scrollean.
app.addEventListener("click", (e) => {
  const a = e.target.closest("a[data-salto]");
  if (!a) return;
  e.preventDefault();
  const det = document.querySelector(a.getAttribute("href"));
  det.open = true;
  det.scrollIntoView({ behavior: "smooth", block: "start" });
});

window.addEventListener("hashchange", () => { render(); window.scrollTo(0, 0); });
// Al volver a la pestaña, refresca datos (el scraper corre cada hora).
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible" && !location.hash.startsWith("#/reunion")) {
    calendario = null;
    for (const k in reuniones) delete reuniones[k];
    if (!app.querySelector("iframe")) render();
  }
});
render();
