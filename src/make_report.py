"""Genera reports/ranking_v0.html a partir de los CSV de data/processed."""
from html import escape
from pathlib import Path

import pandas as pd

from ranking import CATEGORIAS, ESCENARIOS, N_SORTEOS, RANGOS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "reports"
TOP = 12

NOMBRE_CAT = {
    "liga": "Ligas",
    "copa_nacional": "Copas nacionales",
    "libertadores": "Libertadores",
    "intercontinental": "Intercontinental",
    "conmebol_2da": "Conmebol 2.ª línea",
    "supercopa_int": "Supercopas internac.",
    "rioplatense": "Rioplatenses",
    "puntos_por_liga": "Puntos históricos que equivalen a una liga",
}
DETALLE_CAT = {
    "copa_nacional": "Copa Argentina, Supercopa, Trofeo de Campeones, Copa de la Liga y las copas viejas de AFA",
    "libertadores": "",
    "intercontinental": "el título mundial de clubes",
    "conmebol_2da": "Sudamericana, Supercopa Sudamericana, Conmebol, Mercosur",
    "supercopa_int": "Recopa, Interamericana, Suruga Bank, Máster, Nicolás Leoz",
    "rioplatense": "Copa Aldao y Escobar-Gerona, contra el campeón uruguayo",
    "puntos_por_liga": "tabla histórica de Primera, recalculada con 3 puntos por victoria",
}


def num(x):
    return f"{x:,.0f}".replace(",", ".") if x >= 1000 else f"{x:g}".replace(".", ",")


def heatmap(mc):
    mc = mc.head(TOP)
    head = "".join(f"<th scope='col'>{p}.º</th>" for p in range(1, TOP + 1))
    rows = []
    for i, (club, r) in enumerate(mc.iterrows()):
        cells = []
        for p in range(1, TOP + 1):
            v = r[str(p)]
            if v < 0.005:
                cells.append("<td class='cero'></td>")
                continue
            pct = "&lt;1" if v < 0.01 else f"{v * 100:.0f}"
            cls = "heat hot" if v > 0.45 else "heat"
            tip = f"{club}: {p}.º en el {v * 100:.0f}% de las ponderaciones"
            cells.append(f"<td class='{cls}' style='--v:{0.1 + 0.9 * v:.3f}' data-tip='{escape(tip, quote=True)}'>{pct}</td>")
        if i in (3, 7):  # cortes que ninguna ponderación cruzó
            rows.append(f"<tr class='sep'><td colspan='{TOP + 1}'></td></tr>")
        rows.append(f"<tr><th scope='row'>{escape(club)}</th>{''.join(cells)}</tr>")
    return f"<table class='mapa'><thead><tr><th></th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def tabla_escenarios(esc):
    esc = esc.head(TOP)
    head = "".join(f"<th scope='col'>{escape(c)}</th>" for c in esc.columns)
    rows = []
    for club, r in esc.iterrows():
        tds = "".join(f"<td>{int(v)}.º</td>" for v in r)
        rows.append(f"<tr><th scope='row'>{escape(club)}</th>{tds}</tr>")
    return f"<table class='datos'><thead><tr><th></th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def tabla_pesos():
    cols = CATEGORIAS + ["puntos_por_liga"]
    head = "".join(f"<th scope='col'>{escape(NOMBRE_CAT[c])}</th>" for c in cols)
    rows = []
    for nombre, pesos in ESCENARIOS.items():
        solo_puntos = not any(pesos[c] for c in CATEGORIAS)
        tds = "".join(f"<td>{num(pesos[c]) if pesos[c] else '—'}</td>" for c in CATEGORIAS)
        tds += f"<td>{'único criterio' if solo_puntos else num(pesos['puntos_por_liga']) if pesos['puntos_por_liga'] else '—'}</td>"
        rows.append(f"<tr><th scope='row'>{escape(nombre)}</th>{tds}</tr>")
    rango = "".join(f"<td>{num(RANGOS[c][0])} a {num(RANGOS[c][1])}</td>" if c in RANGOS else "<td>1 (fijo)</td>" for c in cols)
    rows.append(f"<tr class='corte'><th scope='row'>Sorteo al azar (rango)</th>{rango}</tr>")
    return f"<table class='datos'><thead><tr><th></th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def tabla_base(base, orden):
    base = base.loc[orden[:TOP]]
    cols = CATEGORIAS + ["pts_3"]
    head = "".join(f"<th scope='col'>{escape(NOMBRE_CAT.get(c, 'Puntos históricos'))}</th>" for c in cols)
    rows = []
    for club, r in base.iterrows():
        tds = "".join(f"<td>{num(r[c]) if r[c] else '—'}</td>" for c in cols)
        rows.append(f"<tr><th scope='row'>{escape(club)}</th>{tds}</tr>")
    return f"<table class='datos'><thead><tr><th></th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def glosario():
    items = "".join(f"<li><b>{escape(NOMBRE_CAT[c])}</b>: {escape(d)}.</li>" for c, d in DETALLE_CAT.items() if d)
    return f"<ul class='glosario'>{items}</ul>"


CSS = """
:root{
  --ground:#f5f8fc; --surface:#ffffff; --ink:#13202f; --muted:#56687c; --rule:#d9e2ec; --rule-strong:#13202f;
  --accent:#1c5cab; --heat-lo:#dbe9fa; --heat-hi:#14498c; --on-hot:#ffffff;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0e141b; --surface:#151d27; --ink:#e7eef6; --muted:#93a4b7; --rule:#26323f; --rule-strong:#e7eef6;
    --accent:#86b6ef; --heat-lo:#1a2a3d; --heat-hi:#9ec5f4; --on-hot:#0e141b;
  }
}
:root[data-theme="dark"]{
  --ground:#0e141b; --surface:#151d27; --ink:#e7eef6; --muted:#93a4b7; --rule:#26323f; --rule-strong:#e7eef6;
  --accent:#86b6ef; --heat-lo:#1a2a3d; --heat-hi:#9ec5f4; --on-hot:#0e141b;
}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:16px;line-height:1.55;padding-inline:20px;padding-block:40px 80px}
main{max-width:920px;margin:0 auto;display:flex;flex-direction:column;gap:44px}
header,section{display:flex;flex-direction:column;gap:14px}
h1,h2,.eyebrow,table th{font-family:"Archivo Narrow","Arial Narrow",sans-serif}
.eyebrow{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0}
h1{font-size:clamp(30px,5vw,44px);line-height:1.08;margin:0;text-wrap:balance;font-weight:700}
h2{font-size:24px;line-height:1.15;margin:0;text-wrap:balance;font-weight:700}
p{margin:0;max-width:66ch}
.lead{font-size:18px}
.nota{color:var(--muted);font-size:14px}
.scroll{overflow-x:auto;background:var(--surface);border:1px solid var(--rule);border-radius:6px;padding:14px}
table{border-collapse:separate;border-spacing:2px;font-variant-numeric:tabular-nums;width:100%}
th{font-weight:600;text-align:left;white-space:nowrap;font-size:14px}
thead th{color:var(--muted);text-align:center;font-size:13px;padding:4px 6px;vertical-align:bottom;white-space:normal}
tbody th{padding-right:14px;font-size:15px}
.mapa td{width:52px;min-width:40px;height:34px;text-align:center;font-size:13px;border-radius:3px}
.mapa td.heat{background:color-mix(in oklab,var(--heat-hi) calc(var(--v)*100%),var(--heat-lo));color:var(--ink);cursor:default}
.mapa td.hot{color:var(--on-hot);font-weight:600}
.mapa td.cero{background:transparent}
.mapa td.heat:hover{outline:2px solid var(--ink);outline-offset:-1px}
tr.corte>*{border-top:2px solid var(--rule-strong)}
.mapa tr.sep td{height:2px;min-width:0;padding:0;border-radius:0;background:var(--rule-strong)}
.datos{border-spacing:0}
.datos td,.datos tbody th{padding:7px 10px;border-top:1px solid var(--rule);text-align:center;font-size:14px}
.datos tbody th{text-align:left}
.escalones{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:0;padding:0;list-style:none}
.escalones li{border-top:3px solid var(--accent);padding-top:10px;display:flex;flex-direction:column;gap:4px}
.escalones b{font-family:"Archivo Narrow","Arial Narrow",sans-serif;font-size:19px;line-height:1.2}
.escalones span{color:var(--muted);font-size:14px}
.glosario{margin:0;padding-left:18px;color:var(--muted);font-size:14px;display:flex;flex-direction:column;gap:4px}
.pendientes{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px;max-width:70ch}
#tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--ground);font-size:13px;padding:6px 9px;border-radius:4px;max-width:260px;z-index:5}
"""

JS = """
const tip=document.getElementById('tip');
document.querySelectorAll('[data-tip]').forEach(td=>{
  td.addEventListener('mousemove',e=>{tip.textContent=td.dataset.tip;tip.hidden=false;
    const x=Math.min(e.clientX+14,innerWidth-270);tip.style.left=x+'px';tip.style.top=(e.clientY+16)+'px';});
  td.addEventListener('mouseleave',()=>{tip.hidden=true;});
});
"""


def main():
    mc = pd.read_csv(DATA / "ranking_montecarlo.csv", index_col="club")
    esc = pd.read_csv(DATA / "ranking_escenarios.csv", index_col="club")
    titulos = pd.read_csv(DATA / "titulos.csv")
    conteo = titulos.pivot_table(index="club", columns="categoria", values="anio", aggfunc="count", fill_value=0)
    puntos = pd.read_csv(DATA / "tabla_historica_profesional.csv", index_col="club").pts_3
    base = conteo.reindex(columns=CATEGORIAS, fill_value=0).join(puntos, how="outer").fillna(0)

    html = f"""<title>Grandeza deportiva argentina</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo+Narrow:wght@500;600;700&family=IBM+Plex+Sans:wght@400;600&display=swap">
<style>{CSS}</style>
<main>
<header>
  <p class="eyebrow">Grandeza · resultados deportivos · era profesional 1931–2026 · versión 0</p>
  <h1>El orden exacto depende de cómo ponderes. Los escalones, no.</h1>
  <p class="lead">Nadie sabe todavía cuántas ligas vale una Libertadores. Entonces, en vez de elegir un número, probamos {num(N_SORTEOS)} juegos de pesos distintos, sorteados dentro de rangos razonables, y miramos en qué puesto queda cada club en cada uno.</p>
  <ul class="escalones">
    <li><b>Boca y River</b><span>Siempre 1.º y 2.º. Cuál va primero depende de cuánto pese lo internacional.</span></li>
    <li><b>Independiente</b><span>3.º en el 96% de los casos. Solo en su escalón.</span></li>
    <li><b>Estudiantes, San Lorenzo, Vélez y Racing</b><span>Se reparten del 4.º al 7.º. Nunca salen de ahí, y el orden entre ellos es lo que de verdad está en discusión.</span></li>
    <li><b>Del 8.º para abajo</b><span>Ningún otro club alcanza el 7.º puesto con ninguna ponderación probada.</span></li>
  </ul>
</header>

<section>
  <h2>En qué puesto queda cada club, según la ponderación</h2>
  <p>Cada celda dice en qué porcentaje de las {num(N_SORTEOS)} ponderaciones el club quedó en ese puesto. Celda vacía: no pasó nunca. Las líneas gruesas marcan los cortes que ninguna ponderación cruzó.</p>
  <div class="scroll">{heatmap(mc)}</div>
  <p class="nota">Ojo con leer de más: los porcentajes dependen de los rangos que elegí para sortear (tabla de abajo), que son una opinión mía y no una medición. Lo firme es lo que no cambia con ningún peso: las celdas vacías.</p>
</section>

<section>
  <h2>Seis ponderaciones con nombre</h2>
  <p>Lo mismo, pero con juegos de pesos concretos para poder discutirlos. «Riquelme» toma literal la idea de que una Libertadores vale diez torneos locales.</p>
  <div class="scroll">{tabla_escenarios(esc)}</div>
</section>

<section>
  <h2>Los pesos usados</h2>
  <p>Todo se mide en ligas: cada número dice cuántas ligas vale un título de esa categoría. La última columna va al revés: cuántos puntos de la tabla histórica hacen falta para igualar una liga.</p>
  <div class="scroll">{tabla_pesos()}</div>
  {glosario()}
</section>

<section>
  <h2>Los datos de base</h2>
  <p>Títulos oficiales de la era profesional por categoría, y puntos históricos de Primera. Son {len(titulos)} títulos, uno por fila en la planilla, con año y subcampeón.</p>
  <div class="scroll">{tabla_base(base, list(mc.index))}</div>
</section>

<section>
  <h2>Lo que todavía está flojo</h2>
  <ul class="pendientes">
    <li><b>Los puntos históricos son aproximados.</b> La tabla de Wikipedia para la era profesional quedó congelada en 2020 y la total está actualizada de forma despareja entre clubes. El error estimado es de hasta un 3%. La solución es reconstruirla temporada por temporada.</li>
    <li><b>Sólo cuentan títulos y puntos.</b> No entran subcampeonatos, finales perdidas, descensos ni años en Primera.</li>
    <li><b>Un título de 1935 vale igual que uno de 2024.</b> No hay ningún ajuste por época ni por dificultad del torneo.</li>
    <li><b>Queda afuera el amateurismo</b> (antes de 1931), por decisión para esta primera versión. Es lo que más cambia para Racing.</li>
    <li><b>Casos discutibles de clasificación:</b> la Copa de Oro 1936 de River figura como liga (según el listado de campeones) aunque otras fuentes la cuentan como copa.</li>
  </ul>
  <p class="nota">Fuentes: Wikipedia en español (campeones de Primera División, copas nacionales, títulos internacionales de clubes argentinos, campeonatos rioplatenses, clasificación histórica), con los totales de títulos verificados club por club contra su cuadro resumen.</p>
</section>
</main>
<div id="tip" hidden></div>
<script>{JS}</script>
"""
    OUT.mkdir(exist_ok=True)
    (OUT / "ranking_v0.html").write_text(html, encoding="utf-8")
    print(OUT / "ranking_v0.html")


if __name__ == "__main__":
    main()
