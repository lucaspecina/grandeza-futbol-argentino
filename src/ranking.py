"""Rankings de resultados deportivos (era profesional) bajo distintas ponderaciones.

Puntaje de un club = suma de (títulos de cada categoría x peso de la categoría)
                     + puntos históricos de liga / PUNTOS_POR_LIGA.
La unidad es "una liga": todos los pesos dicen cuántas ligas vale cada cosa.

Dos salidas:
  1. ranking_escenarios.csv  -> unos pocos juegos de pesos con nombre, elegidos a mano.
  2. ranking_montecarlo.csv  -> miles de juegos de pesos al azar dentro de rangos razonables;
     para cada club, en qué proporción de esos mundos queda 1.º, 2.º, 3.º, etc.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

CATEGORIAS = ["liga", "copa_nacional", "libertadores", "intercontinental", "conmebol_2da", "supercopa_int", "rioplatense"]

# pesos en "ligas"; puntos_por_liga = cuántos puntos históricos (3-1-0) equivalen a una liga (None = no cuentan)
ESCENARIOS = {
    "Conteo simple": dict(liga=1, copa_nacional=1, libertadores=1, intercontinental=1, conmebol_2da=1, supercopa_int=1, rioplatense=1, puntos_por_liga=None),
    "Solo ligas": dict(liga=1, copa_nacional=0, libertadores=0, intercontinental=0, conmebol_2da=0, supercopa_int=0, rioplatense=0, puntos_por_liga=None),
    "Moderado": dict(liga=1, copa_nacional=0.4, libertadores=3, intercontinental=3, conmebol_2da=1.2, supercopa_int=0.5, rioplatense=0.4, puntos_por_liga=None),
    "Riquelme (Lib = 10 ligas)": dict(liga=1, copa_nacional=0.4, libertadores=10, intercontinental=10, conmebol_2da=3, supercopa_int=1, rioplatense=0.4, puntos_por_liga=None),
    "Solo puntos históricos": dict(liga=0, copa_nacional=0, libertadores=0, intercontinental=0, conmebol_2da=0, supercopa_int=0, rioplatense=0, puntos_por_liga=1),
    "Moderado + regularidad": dict(liga=1, copa_nacional=0.4, libertadores=3, intercontinental=3, conmebol_2da=1.2, supercopa_int=0.5, rioplatense=0.4, puntos_por_liga=150),
}

# Monte Carlo: rango (mín, máx) de cada peso, en ligas. Se sortea en escala logarítmica
# (que valga 2 o 0,5 es igual de probable). La liga queda fija en 1 porque es la unidad.
RANGOS = dict(
    copa_nacional=(0.1, 1),
    libertadores=(1, 10),
    intercontinental=(0.5, 10),
    conmebol_2da=(0.3, 3),
    supercopa_int=(0.1, 1.5),
    rioplatense=(0.1, 1),
    puntos_por_liga=(50, 500),
)
N_SORTEOS = 20_000


def cargar():
    titulos = pd.read_csv(DATA / "titulos.csv")
    conteo = titulos.pivot_table(index="club", columns="categoria", values="anio", aggfunc="count", fill_value=0)
    conteo = conteo.reindex(columns=CATEGORIAS, fill_value=0)
    puntos = pd.read_csv(DATA / "tabla_historica_profesional.csv", index_col="club").pts_3
    base = conteo.join(puntos, how="outer").fillna(0)
    return base


def puntaje(base, pesos):
    s = sum(base[c] * pesos[c] for c in CATEGORIAS)
    if pesos.get("puntos_por_liga"):
        s = s + base.pts_3 / pesos["puntos_por_liga"]
    return s


def escenarios(base):
    out = {}
    for nombre, pesos in ESCENARIOS.items():
        out[nombre] = puntaje(base, pesos).rank(ascending=False, method="min").astype(int)
    return pd.DataFrame(out)


def montecarlo(base, seed=0):
    rng = np.random.default_rng(seed)
    n = N_SORTEOS
    W = {c: np.exp(rng.uniform(np.log(a), np.log(b), n)) for c, (a, b) in RANGOS.items()}
    W["liga"] = np.ones(n)
    # restricción de orden: la segunda línea de Conmebol no puede valer más que la Libertadores
    W["conmebol_2da"] = np.minimum(W["conmebol_2da"], W["libertadores"])
    X = np.stack([base[c].to_numpy() for c in CATEGORIAS])  # categorias x clubes
    S = sum(np.outer(W[c], X[i]) for i, c in enumerate(CATEGORIAS))  # sorteos x clubes
    S = S + np.outer(1 / W["puntos_por_liga"], base.pts_3.to_numpy())
    pos = (-S).argsort(axis=1).argsort(axis=1) + 1  # posición de cada club en cada sorteo
    max_pos = 12
    tabla = pd.DataFrame(
        {p: (pos == p).mean(axis=0) for p in range(1, max_pos + 1)}, index=base.index
    )
    tabla["pos_media"] = pos.mean(axis=0)
    tabla["pos_mejor"] = pos.min(axis=0)
    tabla["pos_peor"] = pos.max(axis=0)
    return tabla.sort_values("pos_media")


def main():
    base = cargar()
    esc = escenarios(base)
    orden = esc.mean(axis=1).sort_values().index
    esc = esc.loc[orden]
    esc.to_csv(DATA / "ranking_escenarios.csv")
    print(esc.head(12).to_string())

    mc = montecarlo(base)
    mc.to_csv(DATA / "ranking_montecarlo.csv")
    print()
    print((mc.head(12).drop(columns=["pos_media", "pos_mejor", "pos_peor"]) * 100).round(0).astype(int).to_string())
    print(mc.head(12)[["pos_media", "pos_mejor", "pos_peor"]].round(2).to_string())


if __name__ == "__main__":
    main()
