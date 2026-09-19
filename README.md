# Grandeza del fútbol argentino

Un intento de definir con datos qué es un «club grande» en Argentina.

**Página pública:** https://lucaspecina.github.io/grandeza-futbol-argentino/

## Estado

Primera etapa: **rendimiento deportivo de la era profesional (1931–2026)**. La página permite elegir
cuántas ligas vale cada competencia y ver cómo cambia el ranking, e incluye un análisis de robustez
con 20.000 ponderaciones sorteadas al azar.

Próximas etapas: reconstruir las posiciones temporada por temporada, sumar otras dimensiones
(socios, hinchas, etc.) y estimar las ponderaciones a partir de preferencias de la gente.

## Cómo reproducirlo

Requiere [uv](https://docs.astral.sh/uv/).

```bash
uv run python src/fetch_wikipedia.py          # baja las páginas fuente a data/raw/wikipedia
uv run python src/build_titulos.py            # data/processed/titulos.csv (una fila por título)
uv run python src/build_tabla_historica.py    # data/processed/tabla_historica_profesional.csv
uv run python src/ranking.py                  # escenarios + sorteo de ponderaciones
cd src && uv run python make_calculadora.py   # docs/index.html (la página pública)
cd src && uv run python make_report.py        # reports/ranking_v0.html (informe interno)
```

## Datos y fuentes

- `data/processed/titulos.csv`: 300 títulos oficiales, con año, competencia, categoría, campeón y subcampeón.
- `data/processed/tabla_historica_profesional.csv`: partidos y puntos de Primera División desde 1931.
  Es aproximada (hasta 3% de error): la fuente está actualizada de forma despareja entre clubes.
- `data/raw/wikipedia/`: copia de las páginas de Wikipedia en español usadas como fuente, con el número
  de revisión exacto en `manifest.json`. Ese contenido es de Wikipedia y se distribuye bajo licencia
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.es).
