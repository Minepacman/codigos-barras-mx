#!/usr/bin/env python3
"""Valida `extra/manual.csv`: columnas, dígito de control, categorías, duplicados.

Uso: python scripts/validar_manual.py [extra/manual.csv]
Sale con código 1 y un mensaje con el número de línea si hay algún error.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from catalogo import catalogo  # noqa: E402


def main() -> int:
    ruta = Path(sys.argv[1] if len(sys.argv) > 1 else "extra/manual.csv")
    if not ruta.is_file():
        print(f"No existe {ruta}")
        return 1
    try:
        filas = catalogo.leer_manual(ruta.read_text(encoding="utf-8"))
    except catalogo.ErrorManual as e:
        print(f"{ruta}: {e}")
        return 1
    except UnicodeDecodeError as e:
        print(f"{ruta}: el archivo debe estar en UTF-8 ({e})")
        return 1
    print(f"{ruta}: {len(filas)} productos válidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
