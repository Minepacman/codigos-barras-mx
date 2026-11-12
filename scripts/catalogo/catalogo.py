"""Construcción del catálogo final a partir de los productos crudos y de `extra/manual.csv`."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from . import categorias, codigos, limpieza

COLUMNAS = [
    "codigo", "nombre", "marca", "cantidad", "unidad", "contenido", "categoria", "imagen", "fuente", "actualizado",
]

# Prioridad al deduplicar: menor = gana.
PRIORIDAD = {"manual": 0, "off": 1, "obf": 2, "opff": 3, "opf": 4}


def fecha_iso(last_modified_t) -> str:
    """Convierte un timestamp Unix de OFF a 'AAAA-MM-DD'; vacío si no hay."""
    if last_modified_t in (None, "", 0, "0"):
        return ""
    try:
        return datetime.fromtimestamp(int(float(last_modified_t)), tz=timezone.utc).strftime("%Y-%m-%d")
    except (ValueError, OverflowError, OSError):
        return ""


def convertir_crudo(p: dict) -> dict | None:
    """Convierte un producto crudo (ver `fuentes.CAMPOS_CRUDOS`) a una fila del catálogo.

    Devuelve None si el código no es válido, el producto está obsoleto o no tiene nombre.
    """
    if p.get("obsolete") in (True, 1, "1", "on", "true", "True"):
        return None
    codigo = codigos.normalizar(p.get("code"))
    if not codigo:
        return None
    nombre = limpieza.limpiar_nombre(p.get("product_name_es") or p.get("product_name"))
    if not nombre:
        return None
    fuente = p.get("fuente") or "off"
    contenido = limpieza.limpiar_texto(p.get("quantity"))
    cantidad, unidad = limpieza.cantidad_desde_off(
        contenido, p.get("product_quantity"), p.get("product_quantity_unit")
    )
    return {
        "codigo": codigo,
        "nombre": nombre,
        "marca": limpieza.limpiar_marca(p.get("brands")),
        "cantidad": cantidad if cantidad is not None else "",
        "unidad": unidad or "",
        "contenido": contenido,
        "categoria": categorias.categoria_para(p.get("categories_tags"), fuente, nombre),
        "imagen": (p.get("imagen") or "").strip(),
        "fuente": fuente,
        "actualizado": fecha_iso(p.get("last_modified_t")),
    }


class ErrorManual(ValueError):
    """Fila inválida en `extra/manual.csv`."""


def leer_manual(texto: str) -> list[dict]:
    """Lee el CSV manual (mismas columnas que el catálogo). Lanza ErrorManual con el número de línea.

    Se ignoran líneas vacías y las que empiezan con '#'.
    """
    lineas = [(n, l) for n, l in enumerate(texto.splitlines(), 1) if l.strip() and not l.lstrip().startswith("#")]
    if not lineas:
        return []
    encabezado = next(csv.reader([lineas[0][1]]))
    faltan = [c for c in COLUMNAS if c not in encabezado]
    if faltan:
        raise ErrorManual(f"línea {lineas[0][0]}: faltan columnas {faltan}")
    filas = []
    vistos: dict[str, int] = {}
    for numero, linea in lineas[1:]:
        valores = next(csv.reader([linea]))
        if len(valores) != len(encabezado):
            raise ErrorManual(f"línea {numero}: {len(valores)} columnas, se esperaban {len(encabezado)}")
        fila = dict(zip(encabezado, valores))
        codigo = codigos.normalizar(fila.get("codigo"))
        if not codigo:
            raise ErrorManual(f"línea {numero}: código inválido {fila.get('codigo')!r} (dígito de control o longitud)")
        if codigo in vistos:
            raise ErrorManual(f"línea {numero}: código {codigo} repetido (ya está en la línea {vistos[codigo]})")
        vistos[codigo] = numero
        nombre = limpieza.limpiar_nombre(fila.get("nombre"))
        if not nombre:
            raise ErrorManual(f"línea {numero}: el nombre no puede estar vacío")
        categoria = (fila.get("categoria") or "").strip() or "Otros"
        if categoria not in categorias.CATEGORIAS:
            raise ErrorManual(f"línea {numero}: categoría {categoria!r} no válida; usa una de {categorias.CATEGORIAS}")
        cantidad_txt = (fila.get("cantidad") or "").strip()
        cantidad: float | int | str = ""
        if cantidad_txt:
            try:
                valor = float(cantidad_txt.replace(",", "."))
            except ValueError as e:
                raise ErrorManual(f"línea {numero}: cantidad {cantidad_txt!r} no es un número") from e
            cantidad = int(valor) if valor == int(valor) else valor
        actualizado = (fila.get("actualizado") or "").strip()
        if actualizado:
            try:
                datetime.strptime(actualizado, "%Y-%m-%d")
            except ValueError as e:
                raise ErrorManual(f"línea {numero}: fecha {actualizado!r} debe ser AAAA-MM-DD") from e
        imagen = (fila.get("imagen") or "").strip()
        if imagen and not imagen.startswith(("http://", "https://")):
            raise ErrorManual(f"línea {numero}: la imagen debe ser una URL http(s)")
        filas.append({
            "codigo": codigo,
            "nombre": nombre,
            "marca": limpieza.limpiar_marca(fila.get("marca")),
            "cantidad": cantidad,
            "unidad": (fila.get("unidad") or "").strip(),
            "contenido": limpieza.limpiar_texto(fila.get("contenido")),
            "categoria": categoria,
            "imagen": imagen,
            "fuente": "manual",
            "actualizado": actualizado,
        })
    return filas


def combinar(filas: list[dict]) -> list[dict]:
    """Deduplica por código (manual > off > obf > opff > opf; a igual fuente, el más reciente) y ordena."""
    por_codigo: dict[str, dict] = {}
    for fila in filas:
        actual = por_codigo.get(fila["codigo"])
        if actual is None or _clave_prioridad(fila) < _clave_prioridad(actual):
            por_codigo[fila["codigo"]] = fila
    return sorted(por_codigo.values(), key=lambda f: f["codigo"])


def _clave_prioridad(fila: dict) -> tuple[int, str]:
    # Fecha invertida para que la más reciente sea "menor".
    return PRIORIDAD.get(fila["fuente"], 9), "".join(chr(255 - ord(c)) for c in (fila["actualizado"] or ""))


def a_csv(filas: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNAS, lineterminator="\n")
    w.writeheader()
    for f in filas:
        w.writerow({c: f.get(c, "") for c in COLUMNAS})
    return buf.getvalue()


def _registro_json(fila: dict) -> dict:
    d = {c: fila.get(c, "") for c in COLUMNAS}
    if d["cantidad"] == "":
        d["cantidad"] = None
    return d


def a_jsonl(filas: list[dict]) -> str:
    return "".join(json.dumps(_registro_json(f), ensure_ascii=False) + "\n" for f in filas)


def fragmentos(filas: list[dict]) -> dict[str, dict]:
    """Agrupa por los últimos 3 dígitos del código → {'075': {'7501055300075': {...}, ...}}."""
    grupos: dict[str, dict] = {}
    for f in filas:
        clave = codigos.clave_fragmento(f["codigo"])
        registro = _registro_json(f)
        del registro["codigo"]
        grupos.setdefault(clave, {})[f["codigo"]] = registro
    return grupos


def a_json_fragmento(productos: dict) -> str:
    return json.dumps(productos, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
