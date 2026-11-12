"""Limpieza de textos (nombre, marca) y análisis de la cantidad ("600 ml", "1 kg", "6 pz")."""

from __future__ import annotations

import re
import unicodedata

_ESPACIOS = re.compile(r"\s+")

# Unidades reconocidas → unidad canónica. Las claves van en minúsculas y sin puntos.
_UNIDADES = {
    "g": "g", "gr": "g", "grs": "g", "gramo": "g", "gramos": "g", "gram": "g", "grams": "g",
    "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogramo": "kg", "kilogramos": "kg",
    "mg": "mg",
    "ml": "ml", "mls": "ml", "mililitro": "ml", "mililitros": "ml", "cc": "ml",
    "cl": "cl",
    "l": "l", "lt": "l", "lts": "l", "ltr": "l", "litro": "l", "litros": "l", "liter": "l", "liters": "l", "litre": "l",
    "oz": "oz", "onza": "oz", "onzas": "oz", "floz": "fl oz", "fl oz": "fl oz",
    "lb": "lb", "lbs": "lb", "libra": "lb", "libras": "lb",
    "pz": "pz", "pza": "pz", "pzas": "pz", "pzs": "pz", "pieza": "pz", "piezas": "pz",
    "u": "pz", "un": "pz", "unidad": "pz", "unidades": "pz", "unit": "pz", "units": "pz",
    "pc": "pz", "pcs": "pz", "piece": "pz", "pieces": "pz", "x": "pz", "ct": "pz",
    "sobres": "pz", "sobre": "pz", "tabletas": "pz", "tabs": "pz", "capsulas": "pz",
    "rollos": "pz", "rollo": "pz", "barras": "pz", "barra": "pz", "latas": "pz", "lata": "pz",
    "botellas": "pz", "botella": "pz", "bolsas": "pz", "bolsa": "pz", "paquetes": "pz", "paquete": "pz",
}

_METRICAS = frozenset({"g", "kg", "mg", "ml", "cl", "l"})

# número (con coma o punto decimal) seguido opcionalmente de espacio y unidad.
_CANTIDAD = re.compile(
    r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s*(fl\s*oz|[a-zA-Záéíóú]+)?(?![\d])",
    re.IGNORECASE,
)
# "6 x 355 ml", "2x1 l", "12 pack x 355ml"
_MULTIPACK = re.compile(
    r"(\d+)\s*(?:x|×|\*|pack(?:s)?\s*(?:x|de)?|piezas?\s*de|pz\s*de|botellas?\s*de|latas?\s*de)\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)",
    re.IGNORECASE,
)


def limpiar_texto(texto: str | None) -> str:
    """Quita espacios repetidos y caracteres de control; conserva mayúsculas/acentos."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFC", str(texto))
    texto = "".join(ch for ch in texto if unicodedata.category(ch)[0] != "C")
    texto = _ESPACIOS.sub(" ", texto).strip(" \t-–—,;:.")
    return texto


def normalizar_mayusculas(texto: str) -> str:
    """Si el texto viene TODO EN MAYÚSCULAS (y tiene más de 3 letras) lo pasa a formato Título."""
    letras = [ch for ch in texto if ch.isalpha()]
    if len(letras) > 3 and all(ch.isupper() for ch in letras):
        return " ".join(_titulo(p) for p in texto.split(" "))
    return texto


def _titulo(palabra: str) -> str:
    if len(palabra) <= 2 and palabra.isalpha():  # "DE", "LA", "Y" → "de", "la", "y"
        return palabra.lower()
    return palabra[:1].upper() + palabra[1:].lower()


def limpiar_nombre(texto: str | None) -> str:
    nombre = normalizar_mayusculas(limpiar_texto(texto))
    if len(nombre) > 200:
        nombre = nombre[:200].rstrip()
    return nombre


def limpiar_marca(texto: str | None) -> str:
    """Primera marca de la lista ("Coca-Cola, The Coca-Cola Company" → "Coca-Cola")."""
    marca = limpiar_texto(texto)
    if "," in marca:
        marca = marca.split(",")[0].strip()
    marca = normalizar_mayusculas(marca)
    return marca[:80]


def _a_numero(texto: str) -> float:
    return float(texto.replace(",", "."))


def _unidad(texto: str | None) -> str | None:
    if not texto:
        return None
    clave = texto.lower().replace(".", "").replace(" ", "")
    if clave == "floz":
        return "fl oz"
    clave = unicodedata.normalize("NFKD", clave).encode("ascii", "ignore").decode()
    return _UNIDADES.get(clave)


def _formatear(valor: float) -> float | int:
    return int(valor) if valor == int(valor) else round(valor, 3)


def analizar_cantidad(texto: str | None) -> tuple[float | int | None, str | None]:
    """Extrae (cantidad, unidad) de un texto como "600 ml", "1,5 L", "6 x 355 ml", "12 piezas".

    En multipacks devuelve el total (6 x 355 ml → 2130 ml). Si no hay unidad reconocible
    pero sí un número suelto, devuelve (número, None). Si no hay número, (None, None).
    """
    if not texto:
        return None, None
    texto = limpiar_texto(texto)
    m = _MULTIPACK.search(texto)
    if m:
        unidad = _unidad(m.group(3))
        if unidad and unidad != "pz":
            total = int(m.group(1)) * _a_numero(m.group(2))
            return _formatear(total), unidad
    # Si hay varias cantidades ("6.5 FL OZ (190 ml)") se prefiere la métrica.
    primera = None
    for m in _CANTIDAD.finditer(texto):
        unidad = _unidad(m.group(2))
        if unidad:
            if unidad in _METRICAS:
                return _formatear(_a_numero(m.group(1))), unidad
            primera = primera or (_formatear(_a_numero(m.group(1))), unidad)
    if primera:
        return primera
    m = _CANTIDAD.search(texto)
    if m:
        return _formatear(_a_numero(m.group(1))), None
    return None, None


def cantidad_desde_off(
    quantity: str | None, product_quantity: str | float | None, product_quantity_unit: str | None
) -> tuple[float | int | None, str | None]:
    """Combina el texto `quantity` con los campos normalizados de OFF (`product_quantity` en g/ml)."""
    cantidad, unidad = analizar_cantidad(quantity)
    if cantidad is not None and unidad:
        return cantidad, unidad
    if product_quantity not in (None, ""):
        try:
            valor = _formatear(float(str(product_quantity).replace(",", ".")))
        except ValueError:
            valor = None
        if valor is not None and valor > 0:
            return valor, _unidad(product_quantity_unit)
    return cantidad, unidad
