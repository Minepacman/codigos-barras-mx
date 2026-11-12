#!/usr/bin/env python3
"""Genera el catálogo (datos/, api/v1/) a partir de los JSONL crudos y de extra/manual.csv.

Uso:
    python scripts/generar.py [--crudo build/crudo] [--manual extra/manual.csv] [--raiz .]

Salidas (relativas a --raiz):
    datos/catalogo-mx.csv, datos/catalogo-mx.jsonl   catálogo completo
    api/v1/<últimos 3 dígitos>.json                 fragmentos para consultas individuales
    api/v1/version.json                             fecha, conteos y sha256 de los archivos completos
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalogo import catalogo  # noqa: E402

LOG = logging.getLogger("generar")


def leer_crudos(carpeta: Path) -> list[dict]:
    filas = []
    descartados = Counter()
    for archivo in sorted(carpeta.glob("*.jsonl")):
        n = 0
        with archivo.open(encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                fila = catalogo.convertir_crudo(json.loads(linea))
                if fila is None:
                    descartados[archivo.stem] += 1
                    continue
                filas.append(fila)
                n += 1
        LOG.info("%s: %d filas válidas, %d descartadas", archivo.name, n, descartados[archivo.stem])
    return filas


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--crudo", default="build/crudo")
    parser.add_argument("--manual", default="extra/manual.csv")
    parser.add_argument("--raiz", default=".")
    parser.add_argument("--minimo", type=int, default=1000,
                        help="aborta si el catálogo tiene menos filas (protege de descargas vacías)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    raiz = Path(args.raiz)
    filas = leer_crudos(Path(args.crudo)) if Path(args.crudo).is_dir() else []
    manual = Path(args.manual)
    if manual.is_file():
        filas_manual = catalogo.leer_manual(manual.read_text(encoding="utf-8"))
        LOG.info("%s: %d filas", manual, len(filas_manual))
        filas.extend(filas_manual)
    final = catalogo.combinar(filas)
    if len(final) < args.minimo:
        LOG.error("Solo %d productos (< %d); no se escribe nada", len(final), args.minimo)
        return 2

    datos = raiz / "datos"
    datos.mkdir(parents=True, exist_ok=True)
    csv_path = datos / "catalogo-mx.csv"
    jsonl_path = datos / "catalogo-mx.jsonl"
    csv_path.write_text(catalogo.a_csv(final), encoding="utf-8")
    jsonl_path.write_text(catalogo.a_jsonl(final), encoding="utf-8")

    api = raiz / "api" / "v1"
    api.mkdir(parents=True, exist_ok=True)
    grupos = catalogo.fragmentos(final)
    for existente in api.glob("*.json"):
        if existente.name != "version.json" and existente.stem not in grupos:
            existente.unlink()
    for clave, productos in grupos.items():
        (api / f"{clave}.json").write_text(catalogo.a_json_fragmento(productos), encoding="utf-8")

    por_fuente = Counter(f["fuente"] for f in final)
    por_categoria = Counter(f["categoria"] for f in final)
    version = {
        "version": 1,
        "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "productos": len(final),
        "por_fuente": dict(sorted(por_fuente.items())),
        "por_categoria": dict(sorted(por_categoria.items())),
        "fragmentos": len(grupos),
        "esquema_fragmentos": "api/v1/<ultimos 3 digitos del codigo normalizado>.json",
        "archivos": {
            "catalogo-mx.csv": {"sha256": sha256(csv_path), "bytes": csv_path.stat().st_size},
            "catalogo-mx.jsonl": {"sha256": sha256(jsonl_path), "bytes": jsonl_path.stat().st_size},
        },
        "atribucion": "Contiene información de Open Food Facts, disponible bajo la Open Database License (ODbL)",
    }
    (api / "version.json").write_text(json.dumps(version, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOG.info("Catálogo: %d productos, %d fragmentos, fuentes %s", len(final), len(grupos), dict(por_fuente))
    print(len(final))
    return 0


if __name__ == "__main__":
    sys.exit(main())
