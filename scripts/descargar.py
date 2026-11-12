#!/usr/bin/env python3
"""Descarga los productos de México de Open Food Facts (y OBF/OPFF/OPF) a archivos JSONL crudos.

Uso:
    python scripts/descargar.py --salida build/crudo [--fuentes off,obf,opff,opf] [--estrategia auto|parquet|busqueda]

Genera `build/crudo/<fuente>.jsonl` (una línea por producto, campos de `catalogo.fuentes.CAMPOS_CRUDOS`).
Los archivos crudos no se versionan; `generar.py` los convierte al catálogo final.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalogo import fuentes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", default="build/crudo", help="carpeta de salida (se crea)")
    parser.add_argument("--fuentes", default="off,obf,opff,opf", help="fuentes separadas por coma")
    parser.add_argument("--estrategia", default="auto", choices=["auto", "parquet", "busqueda"])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    fallos = []
    for fuente in [f.strip() for f in args.fuentes.split(",") if f.strip()]:
        t0 = time.time()
        try:
            productos = fuentes.descargar(fuente, args.estrategia)
        except Exception as e:  # noqa: BLE001
            logging.error("Fuente %s falló: %s", fuente, e)
            fallos.append(fuente)
            continue
        destino = salida / f"{fuente}.jsonl"
        with destino.open("w", encoding="utf-8") as f:
            for p in productos:
                f.write(json.dumps(p, ensure_ascii=False, default=str) + "\n")
        logging.info("%s: %d productos → %s (%.0f s)", fuente, len(productos), destino, time.time() - t0)
    if fallos:
        logging.error("Fuentes con error: %s", ", ".join(fallos))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
