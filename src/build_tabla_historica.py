"""Arma data/processed/tabla_historica_profesional.csv: partidos de liga 1931-2025 por club.

Problema: la tabla "era profesional" de Wikipedia quedó congelada en abril de 2020.
La tabla total (1891-2025) sí está al día, y la amateur (1891-1934) no cambia más.
Entonces: profesional = total - amateur. Se valida contra la tabla de 2020: para los
clubes que no jugaron en Primera desde entonces, tiene que dar exactamente igual.

Los puntos se recalculan con un mismo criterio para todas las épocas (la tabla original
mezcla 2 y 3 puntos por victoria): pts_3 = 3G + E, pts_2 = 2G + E.
"""
import re
from io import StringIO
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "wikipedia"
OUT = ROOT / "data" / "processed"
STATS = ["PJ", "G", "E", "P"]  # los goles de la tabla amateur tienen errores evidentes; no se usan
ALIAS = {"Colón (SF)": "Colón", "Deportivo Riestra": "Riestra"}


def prep(t):
    t = t.copy()
    t.columns = [re.sub(r"\[.*?\]|\u200b", "", str(c)).strip() for c in t.columns]
    t["Club"] = t.Club.astype(str).str.replace(r"\[.*?\]|\u200b", "", regex=True).str.strip().replace(ALIAS)
    for c in STATS:
        sin_miles = t[c].astype(str).str.replace(r"(?<=\d)[.\s](?=\d{3}\b)", "", regex=True)  # "2.941" -> 2941
        t[c] = pd.to_numeric(sin_miles, errors="coerce")
    return t[t.PJ.notna()].set_index("Club")[STATS]


def main():
    ts = pd.read_html(StringIO((RAW / "clasificacion_historica.html").read_text(encoding="utf-8")))
    amateur, pro2020, total = prep(ts[0]), prep(ts[1]), prep(ts[2])

    rows = {}
    for nombre, fila in total.iterrows():
        # "Banfield + Banfield Athletic": la tabla total fusiona clubes; el primero es el actual.
        partes = [p.strip() for p in nombre.split(" + ")]
        am = amateur.reindex(partes).fillna(0).sum()
        rows[partes[0]] = fila - am
    pro = pd.DataFrame(rows).T
    pro = pro[pro.PJ > 0]

    # Validación contra la tabla congelada de 2020.
    comunes = pro.index.intersection(pro2020.index)
    diff = pro.loc[comunes, "PJ"] - pro2020.loc[comunes, "PJ"]
    print(f"clubes: {len(pro)} | iguales a 2020: {(diff == 0).sum()} | con partidos nuevos: {(diff > 0).sum()}")
    raros = diff[diff < 0]
    if len(raros):
        print("OJO, menos partidos que en 2020 (se usa la tabla 2020):", raros.to_dict())
        pro.loc[raros.index] = pro2020.loc[raros.index]
    faltan = pro2020.index.difference(pro.index)
    if len(faltan):
        print("sólo en tabla 2020 (se agregan):", list(faltan))
        pro = pd.concat([pro, pro2020.loc[faltan]])

    pro = pro.astype(int)
    pro["pts_3"] = 3 * pro.G + pro.E
    pro["pts_2"] = 2 * pro.G + pro.E
    pro["pts_por_partido"] = (pro.pts_3 / pro.PJ).round(3)
    pro = pro.sort_values("pts_3", ascending=False).rename_axis("club")
    OUT.mkdir(parents=True, exist_ok=True)
    pro.to_csv(OUT / "tabla_historica_profesional.csv")
    print(pro.head(15).to_string())


if __name__ == "__main__":
    main()
