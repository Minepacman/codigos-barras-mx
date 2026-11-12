#!/usr/bin/env python3
"""Comprime el catálogo completo para publicarlo como Release y escribe los checksums.

Uso: python scripts/empaquetar.py [--salida build/release]

Produce catalogo-mx.csv.gz, catalogo-mx.jsonl.gz, version.json y SHA256SUMS.txt.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
import sys
from pathlib import Path


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", default="datos")
    parser.add_argument("--version", default="api/v1/version.json")
    parser.add_argument("--salida", default="build/release")
    args = parser.parse_args()
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    generados = []
    for nombre in ("catalogo-mx.csv", "catalogo-mx.jsonl"):
        origen = Path(args.datos) / nombre
        destino = salida / f"{nombre}.gz"
        with origen.open("rb") as f_in, gzip.GzipFile(destino, "wb", mtime=0, compresslevel=9) as f_out:
            shutil.copyfileobj(f_in, f_out)
        generados.append(destino)
    version = Path(args.version)
    if version.is_file():
        shutil.copy(version, salida / "version.json")
        generados.append(salida / "version.json")
    lineas = [f"{sha256(g)}  {g.name}" for g in generados]
    (salida / "SHA256SUMS.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    for g in generados:
        print(f"{g} ({g.stat().st_size / 1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
