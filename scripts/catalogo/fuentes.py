"""Descarga de productos de México desde Open Food Facts y proyectos hermanos.

Dos estrategias, de la más eficiente a la de respaldo:

1. `descargar_parquet`: consulta con DuckDB (httpfs, peticiones HTTP por rangos) la exportación
   Parquet diaria publicada en Hugging Face (`openfoodfacts/product-database`), pidiendo solo las
   columnas necesarias y filtrando por `countries_tags` ∋ en:mexico o código con prefijo GS1 750.
   Medido (2026-11): ~4 min y ~7 GB transferidos; con grupos de filas de 1024 filas la proyección
   de columnas casi no reduce la transferencia, pero no carga los servidores de OFF y encuentra
   ~50 % más productos que la búsqueda por país (prefijo 750 sin etiqueta de país).
2. `descargar_busqueda`: API de búsqueda (`/cgi/search.pl?...&json=1`) paginada, respetando el
   límite de 10 búsquedas por minuto (~20 min para OFF, pocos MB). Es el único camino para Open
   Products Facts (no hay Parquet) y el respaldo si el Parquet falla.

Ambas devuelven una lista de diccionarios "crudos" homogéneos (ver `CAMPOS_CRUDOS`).
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterable

import requests

LOG = logging.getLogger("catalogo.fuentes")

USER_AGENT = "PuntoDeVenta-Catalogo/1.0 (https://github.com/Minepacman/codigos-barras-mx)"

# fuente → (dominio de búsqueda, archivo parquet en Hugging Face o None)
FUENTES = {
    "off": ("https://world.openfoodfacts.org", "food.parquet"),
    "obf": ("https://world.openbeautyfacts.org", "beauty.parquet"),
    "opff": ("https://world.openpetfoodfacts.org", "petfood.parquet"),
    "opf": ("https://world.openproductsfacts.org", None),
}

# Servidor de imágenes de cada proyecto.
HOST_IMAGENES = {
    "off": "https://images.openfoodfacts.org",
    "obf": "https://images.openbeautyfacts.org",
    "opff": "https://images.openpetfoodfacts.org",
    "opf": "https://images.openproductsfacts.org",
}

HF_BASE = "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/"

CAMPOS_CRUDOS = [
    "code", "lang", "product_name", "product_name_es", "brands", "quantity", "product_quantity",
    "product_quantity_unit", "categories_tags", "countries_tags", "imagen", "last_modified_t", "obsolete",
]

# Pausa entre búsquedas: el límite público es 10 búsquedas/min por IP.
PAUSA_BUSQUEDA_S = 6.5
TAMANO_PAGINA = 100

FILTRO_SQL = "(list_contains(countries_tags, 'en:mexico') OR code LIKE '750%')"


def _sesion() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


# ---------------------------------------------------------------------------
# Estrategia 1: Parquet remoto con DuckDB
# ---------------------------------------------------------------------------

def url_directa_parquet(archivo: str) -> str:
    """Resuelve la redirección de Hugging Face una sola vez y devuelve la URL firmada del CDN.

    Cada petición por rangos de DuckDB contra la URL `resolve/` cuenta para el límite de
    3000 resoluciones por 5 minutos de Hugging Face (y da HTTP 429); contra la URL firmada del
    CDN no hay ese límite. La URL firmada caduca en ~1 h, suficiente para la consulta.
    Si existe `HF_TOKEN` en el entorno se usa (los límites son más amplios con sesión).
    """
    import os

    cabeceras = {"User-Agent": USER_AGENT}
    token = os.environ.get("HF_TOKEN")
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    r = requests.head(HF_BASE + archivo, headers=cabeceras, allow_redirects=False, timeout=60)
    if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
        return r.headers["Location"]
    r.raise_for_status()
    return HF_BASE + archivo


def descargar_parquet(fuente: str, hilos: int = 8) -> list[dict]:
    """Lee los productos de México del Parquet de `fuente` ('off', 'obf' u 'opff')."""
    import duckdb  # import tardío: solo hace falta en esta estrategia

    archivo = FUENTES[fuente][1]
    if archivo is None:
        raise ValueError(f"{fuente} no tiene exportación Parquet")
    url = url_directa_parquet(archivo)
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET threads={hilos};")
    con.execute("SET http_keep_alive=true;")
    con.execute("SET http_retries=5;")
    con.execute("SET http_retry_wait_ms=2000;")
    con.execute("SET http_timeout=120000;")
    con.execute("SET enable_progress_bar=false;")
    con.execute("SET allow_asterisks_in_http_paths=true;")  # la URL firmada del CDN lleva "*"
    sql = f"""
        SELECT
            code,
            lang,
            list_filter(product_name, lambda x: x.lang = 'main')[1].text AS product_name,
            list_filter(product_name, lambda x: x.lang = 'es')[1].text   AS product_name_es,
            brands,
            quantity,
            product_quantity,
            product_quantity_unit,
            categories_tags,
            countries_tags,
            list_transform(list_filter(images, lambda i: i.key LIKE 'front%'),
                           lambda i: struct_pack(key := i.key, rev := i.rev)) AS imagenes,
            last_modified_t,
            obsolete
        FROM read_parquet(?)
        WHERE {FILTRO_SQL}
    """
    t0 = time.time()
    LOG.info("DuckDB: consultando %s …", HF_BASE + archivo)
    cur = con.execute(sql, [url])
    columnas = [d[0] for d in cur.description]
    filas = cur.fetchall()
    LOG.info("DuckDB: %d filas de %s en %.0f s", len(filas), archivo, time.time() - t0)
    productos = []
    for fila in filas:
        d = dict(zip(columnas, fila))
        imagenes = d.pop("imagenes") or []
        d["imagen"] = url_imagen(d["code"], d.get("lang"), [(i["key"], i["rev"]) for i in imagenes], fuente)
        d["fuente"] = fuente
        productos.append(d)
    return productos


def carpeta_imagen(code: str) -> str:
    """Carpeta de imágenes de OFF: 13+ dígitos → 750/105/530/0075; códigos cortos → el código."""
    if len(code) >= 13:
        return f"{code[0:3]}/{code[3:6]}/{code[6:9]}/{code[9:]}"
    return code


def url_imagen(code: str, lang: str | None, frontales: Iterable[tuple[str, object]], fuente: str = "off") -> str:
    """URL de la miniatura (200 px) de la imagen frontal, prefiriendo español.

    `frontales` son pares (clave, rev) como ("front_es", 12). Devuelve "" si no hay imagen.
    """
    frontales = [(k, r) for k, r in frontales if k and k.startswith("front")]
    if not frontales:
        return ""
    preferencia = ["front_es", f"front_{lang}" if lang else "", "front_en", "front"]
    elegida = None
    for clave in preferencia:
        if not clave:
            continue
        for k, r in frontales:
            if k == clave:
                elegida = (k, r)
                break
        if elegida:
            break
    if elegida is None:
        elegida = frontales[0]
    clave, rev = elegida
    rev = int(rev) if rev not in (None, "") else None
    nombre = f"{clave}.{rev}.200.jpg" if rev is not None else f"{clave}.200.jpg"
    return f"{HOST_IMAGENES[fuente]}/images/products/{carpeta_imagen(code)}/{nombre}"


# ---------------------------------------------------------------------------
# Estrategia 2: API de búsqueda paginada
# ---------------------------------------------------------------------------

_CAMPOS_API = ",".join([
    "code", "lang", "product_name", "product_name_es", "brands", "quantity", "product_quantity",
    "product_quantity_unit", "categories_tags", "countries_tags", "image_front_small_url",
    "last_modified_t", "obsolete",
])


def _pagina(sesion: requests.Session, dominio: str, pagina: int, filtro: dict) -> dict:
    params = {
        "action": "process", "json": "1", "page": pagina, "page_size": TAMANO_PAGINA,
        "fields": _CAMPOS_API, "sort_by": "created_t", **filtro,
    }
    for intento in range(5):
        try:
            r = sesion.get(f"{dominio}/cgi/search.pl", params=params, timeout=90)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
                return r.json()
            LOG.warning("%s página %d: HTTP %s (intento %d)", dominio, pagina, r.status_code, intento + 1)
        except (requests.RequestException, json.JSONDecodeError) as e:
            LOG.warning("%s página %d: %s (intento %d)", dominio, pagina, e, intento + 1)
        time.sleep(PAUSA_BUSQUEDA_S * (intento + 2))
    raise RuntimeError(f"No se pudo leer la página {pagina} de {dominio}")


def descargar_busqueda(fuente: str, max_paginas: int | None = None) -> list[dict]:
    """Descarga por la API de búsqueda todos los productos con país México de `fuente`."""
    dominio = FUENTES[fuente][0]
    sesion = _sesion()
    filtro = {"tagtype_0": "countries", "tag_contains_0": "contains", "tag_0": "mexico"}
    productos: list[dict] = []
    pagina = 1
    total_paginas = None
    t0 = time.time()
    while True:
        datos = _pagina(sesion, dominio, pagina, filtro)
        if total_paginas is None:
            total = int(datos.get("count", 0))
            total_paginas = max(1, -(-total // TAMANO_PAGINA))
            LOG.info("%s: %d productos en %d páginas", fuente, total, total_paginas)
        for p in datos.get("products", []):
            productos.append({
                "code": p.get("code"), "lang": p.get("lang"),
                "product_name": p.get("product_name"), "product_name_es": p.get("product_name_es"),
                "brands": p.get("brands"), "quantity": p.get("quantity"),
                "product_quantity": p.get("product_quantity"),
                "product_quantity_unit": p.get("product_quantity_unit"),
                "categories_tags": p.get("categories_tags") or [],
                "countries_tags": p.get("countries_tags") or [],
                "imagen": p.get("image_front_small_url") or "",
                "last_modified_t": p.get("last_modified_t"),
                "obsolete": p.get("obsolete") in (True, 1, "1", "on"),
                "fuente": fuente,
            })
        if pagina >= total_paginas or not datos.get("products"):
            break
        if max_paginas and pagina >= max_paginas:
            break
        pagina += 1
        time.sleep(PAUSA_BUSQUEDA_S)
    LOG.info("%s: %d productos en %.0f s", fuente, len(productos), time.time() - t0)
    return productos


def descargar(fuente: str, estrategia: str = "auto") -> list[dict]:
    """Descarga `fuente` con la estrategia pedida ('parquet', 'busqueda' o 'auto' = parquet y si falla, búsqueda)."""
    tiene_parquet = FUENTES[fuente][1] is not None
    if estrategia == "parquet" or (estrategia == "auto" and tiene_parquet):
        try:
            return descargar_parquet(fuente)
        except Exception as e:  # noqa: BLE001 - cualquier fallo de red/DuckDB pasa al respaldo
            if estrategia == "parquet":
                raise
            LOG.warning("Parquet de %s falló (%s); usando la API de búsqueda", fuente, e)
    return descargar_busqueda(fuente)
