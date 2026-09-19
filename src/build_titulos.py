"""Arma data/processed/titulos.csv: una fila por título oficial de la era profesional (1931+).

Columnas: anio, competicion, tipo, categoria, club, subcampeon, temporada
  tipo = liga | copa_nacional | internacional | rioplatense
  categoria = agrupación más fina, que es la unidad a la que después se le pone un peso:
    liga, copa_nacional, libertadores, intercontinental,
    conmebol_2da (segunda línea: Sudamericana, Supercopa Sudamericana, Conmebol, Mercosur),
    supercopa_int (a partido único o mini-torneo: Recopa, Interamericana, Suruga, Máster, N. Leoz),
    rioplatense

Fuente: tablas de Wikipedia (es) bajadas por fetch_wikipedia.py.
"""
import re
from io import StringIO
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "wikipedia"
OUT = ROOT / "data" / "processed"

# Nombre canónico de cada club (las páginas usan variantes distintas).
ALIAS = {
    "Estudiantes de La Plata": "Estudiantes (LP)",
    "Gimnasia y Esgrima La Plata": "Gimnasia y Esgrima (LP)",
    "Gimnasia y Esgrima de La Plata": "Gimnasia y Esgrima (LP)",
    "Talleres de Córdoba": "Talleres (C)",
    "Talleres (Córdoba)": "Talleres (C)",
    "Talleres": "Talleres (C)",
    "Arsenal de Sarandí": "Arsenal",
    "Newell's": "Newell's Old Boys",
    "Central Córdoba (Santiago del Estero)": "Central Córdoba (SdE)",
}


def tables(slug):
    return pd.read_html(StringIO((RAW / f"{slug}.html").read_text(encoding="utf-8")))


def clean_club(s):
    if pd.isna(s):
        return None
    s = re.sub(r"\[[^\]]*\]", "", str(s))  # referencias [107]
    s = re.sub(r"\s*\(\d+\)", "", s.strip())  # puntos "(50)"
    s = s.split(" - ")[0]  # título compartido con un combinado de liga regional (Ibarguren 1952)
    s = s.replace("\u200b", "").strip()
    return ALIAS.get(s, s) or None


def clean_text(s):
    s = re.sub(r"\[[^\]]*\]", "", str(s)).replace("\u200b", "")
    return re.sub(r"\s+", " ", s).strip()


def first_year(s):
    return int(re.search(r"(18|19|20)\d\d", str(s)).group(0))


def liga():
    rows = []
    for t in tables("primera_division"):
        cols = [str(c) for c in t.columns]
        if cols[:2] != ["Temporada", "Torneo"] or "Tercero" not in cols:
            continue
        for _, r in t.iterrows():
            club = clean_club(r["Campeón"])
            if club is None:
                continue
            temporada = clean_text(r["Temporada"])
            anio = first_year(temporada)
            if anio < 1931 or "AFAP" in temporada:
                continue  # amateurismo (incluye la liga amateur paralela de 1931-34, la AFAP)
            torneo = clean_text(r["Torneo"])
            # En temporadas "1991-92" el Clausura se juega en el segundo año.
            if re.search(r"\d{4}-\d{2}", temporada) and torneo != "Apertura":
                anio += 1
            rows.append(
                dict(anio=anio, competicion=f"Primera División ({torneo})", tipo="liga", club=club,
                     subcampeon=clean_club(r["Subcampeón"]), temporada=temporada)
            )
    return pd.DataFrame(rows)


def copas_nacionales():
    t = tables("copas_nacionales")[2]  # copas de Primera División en el profesionalismo
    rows = []
    for _, r in t.iterrows():
        campeon = clean_club(r["Campeón"])
        if campeon is None:
            continue
        temporada = clean_text(r["Temporada"])
        rows.append(
            dict(anio=first_year(temporada), competicion=clean_text(r["Torneo"]), tipo="copa_nacional",
                 club=campeon, subcampeon=clean_club(r["Subcampeón"]), temporada=temporada)
        )
    return pd.DataFrame(rows)


def internacionales():
    rows = []
    for t in tables("internacionales_ganadores"):
        if not isinstance(t.columns, pd.MultiIndex) or "Periodo" not in str(t.columns[0][0]):
            continue
        t.columns = [c[1] for c in t.columns]
        for _, r in t.iterrows():
            titulo = clean_text(r["Título"])
            rows.append(
                dict(anio=first_year(r["Fecha"]), competicion=re.sub(r"\s*(18|19|20)\d\d.*$", "", titulo),
                     tipo="internacional", club=clean_club(r["Club"]), subcampeon=None, temporada=titulo)
            )
    return pd.DataFrame(rows)


def rioplatenses():
    """Copas AFA-AUF (campeón argentino vs. campeón uruguayo). Sólo ediciones definidas."""
    t = tables("rioplatenses")
    fuentes = {"Copa Aldao": t[6], "Copa de Confraternidad Escobar-Gerona": t[10]}
    rows = []
    for competicion, tabla in fuentes.items():
        resultado = [c for c in tabla.columns if c.startswith("Resultado")][0]
        for _, r in tabla.iterrows():
            anio = first_year(r["Año"])
            ganador = re.sub(r"\s*(Argentina|Uruguay)\s*$", "", clean_text(r["Ganador"]))
            if anio < 1931 or "No se disputó" in str(r[resultado]):
                continue
            if ganador in ("Nacional", "Peñarol"):
                continue
            finalista = re.sub(r"\s*(Argentina|Uruguay)\s*$", "", clean_text(r["Finalista"]))
            rows.append(dict(anio=anio, competicion=competicion, tipo="rioplatense", club=clean_club(ganador),
                             subcampeon=finalista, temporada=str(anio)))
    return pd.DataFrame(rows)


CATEGORIA_INTERNACIONAL = {
    "Copa Libertadores": "libertadores",
    "Copa Intercontinental": "intercontinental",
    "Copa Sudamericana": "conmebol_2da",
    "Supercopa Sudamericana": "conmebol_2da",
    "Copa Conmebol": "conmebol_2da",
    "Copa Mercosur": "conmebol_2da",
    "Recopa Sudamericana": "supercopa_int",
    "Copa Interamericana": "supercopa_int",
    "Copa Suruga Bank": "supercopa_int",
    "Copa Máster de Supercopa": "supercopa_int",
    "Copa de Oro Nicolás Leoz": "supercopa_int",
}

# Combinados de ligas regionales que ganaron la Copa Ibarguren: no son clubes.
NO_CLUBES = {"Liga Cordobesa", "Liga Mendocina"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.concat([liga(), copas_nacionales(), internacionales(), rioplatenses()], ignore_index=True)
    df = df[~df.club.isin(NO_CLUBES)]
    df["categoria"] = df.competicion.map(CATEGORIA_INTERNACIONAL).fillna(df.tipo)
    assert not (df.categoria == "internacional").any(), df[df.categoria == "internacional"].competicion.unique()
    df = df[["anio", "competicion", "tipo", "categoria", "club", "subcampeon", "temporada"]]
    df = df.sort_values(["anio", "tipo", "competicion"]).reset_index(drop=True)
    df.to_csv(OUT / "titulos.csv", index=False)
    print(f"{len(df)} títulos -> {OUT / 'titulos.csv'}")
    print(df.groupby("tipo").size().to_string())


if __name__ == "__main__":
    main()
