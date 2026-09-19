"""Baja las páginas de Wikipedia (es) que usamos como fuente, ya renderizadas a HTML.

Guarda cada página en data/raw/wikipedia/<slug>.html y un manifest.json con el
revid (versión exacta de la página) para que el dataset sea reproducible.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "wikipedia"
API = "https://es.wikipedia.org/w/api.php"
UA = "grandeza-futbol-research/0.1 (github.com/lucaspecina)"

PAGES = {
    "primera_division": "Primera División de Argentina",
    "copas_nacionales": "Copas nacionales del fútbol argentino",
    "internacionales_ganadores": "Anexo:Clubes argentinos de fútbol ganadores de competiciones internacionales",
    "estadisticas_equipos": "Anexo:Estadísticas de los equipos de la primera categoría del fútbol argentino",
    "clasificacion_historica": "Anexo:Clasificación histórica de la Primera División de Argentina de fútbol",
}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for slug, title in PAGES.items():
        r = requests.get(
            API,
            params={"action": "parse", "page": title, "prop": "text|revid", "format": "json", "formatversion": 2},
            headers={"User-Agent": UA},
            timeout=60,
        )
        r.raise_for_status()
        parsed = r.json()["parse"]
        (RAW / f"{slug}.html").write_text(parsed["text"], encoding="utf-8")
        manifest[slug] = {
            "title": title,
            "revid": parsed["revid"],
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"{slug}: revid {parsed['revid']}, {len(parsed['text']):,} chars")
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
