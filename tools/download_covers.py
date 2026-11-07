#!/usr/bin/env python3
"""Descarga las carátulas del catálogo a assets/covers/<sistema>/."""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASES = {
    "gb": "https://thumbnails.libretro.com/Nintendo%20-%20Game%20Boy/Named_Boxarts/",
    "gbc": "https://thumbnails.libretro.com/Nintendo%20-%20Game%20Boy%20Color/Named_Boxarts/",
    "gba": "https://thumbnails.libretro.com/Nintendo%20-%20Game%20Boy%20Advance/Named_Boxarts/",
    "nds": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%20DS/Named_Boxarts/",
    "3ds": "https://thumbnails.libretro.com/Nintendo%20-%20Nintendo%203DS/Named_Boxarts/",
}


def main() -> int:
    catalog = json.loads((ROOT / 'data/catalog.json').read_text())
    pairs = [(game['consoleKey'], urllib.parse.unquote(Path(game['cover']).name)) for game in catalog['games']]

    seen: set[tuple[str, str]] = set()
    ok = skipped = failed = 0
    for system, filename in pairs:
        key = (system, filename)
        if key in seen:
            continue
        seen.add(key)

        dest = ROOT / "assets" / "covers" / system / filename
        if dest.exists() and dest.stat().st_size > 1024:
            skipped += 1
            continue

        url = BASES[system] + urllib.parse.quote(filename)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 PokeLauncher"})
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read()
            if len(data) < 1024:
                raise ValueError(f"respuesta demasiado pequeña ({len(data)} bytes)")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            ok += 1
            print(f"OK   {system}/{filename} ({len(data) // 1024} KB)")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {system}/{filename}: {exc}", file=sys.stderr)

    print(f"\nDescargadas: {ok} · Ya existían: {skipped} · Fallidas: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
