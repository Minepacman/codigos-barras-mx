"""Normalización y validación de códigos de barras (EAN-13, UPC-A, EAN-8).

Reglas:
- Se eliminan espacios y cualquier carácter que no sea dígito.
- UPC-A (12 dígitos) se convierte a EAN-13 anteponiendo un cero.
- 8 dígitos se conservan como EAN-8 si su dígito de control es válido; si no lo es y empiezan
  con 0 o 1 se prueban como UPC-E (se expanden a UPC-A y luego a EAN-13).
- Códigos de 13 dígitos con ceros a la izquierda de más (p. ej. "0000012345678")
  no se recortan: deben validar su dígito de control como EAN-13.
- Cualquier otra longitud o un dígito de control incorrecto → None.
"""

from __future__ import annotations

import re

_NO_DIGITOS = re.compile(r"[^0-9]")


def digito_control(cuerpo: str) -> int:
    """Dígito de control GS1 (módulo 10, pesos 3/1 desde la derecha).

    `cuerpo` son los dígitos sin el dígito de control (7 para EAN-8, 11 para
    UPC-A, 12 para EAN-13).
    """
    suma = 0
    for i, ch in enumerate(reversed(cuerpo)):
        peso = 3 if i % 2 == 0 else 1
        suma += int(ch) * peso
    return (10 - suma % 10) % 10


def es_valido(codigo: str) -> bool:
    """True si `codigo` (solo dígitos, 8/12/13) tiene dígito de control correcto."""
    if not codigo or not codigo.isdigit() or len(codigo) not in (8, 12, 13):
        return False
    return digito_control(codigo[:-1]) == int(codigo[-1])


def expandir_upce(upce: str) -> str | None:
    """Expande un UPC-E de 8 dígitos (con sistema numérico y control) a UPC-A."""
    if len(upce) != 8 or upce[0] not in "01":
        return None
    ns, cuerpo, control = upce[0], upce[1:7], upce[7]
    ultimo = cuerpo[5]
    if ultimo in "012":
        upca = ns + cuerpo[0:2] + ultimo + "0000" + cuerpo[2:5]
    elif ultimo == "3":
        upca = ns + cuerpo[0:3] + "00000" + cuerpo[3:5]
    elif ultimo == "4":
        upca = ns + cuerpo[0:4] + "00000" + cuerpo[4]
    else:
        upca = ns + cuerpo[0:5] + "0000" + ultimo
    return upca + control


def normalizar(texto: str | None) -> str | None:
    """Devuelve el código normalizado (EAN-13 o EAN-8) o None si no es válido."""
    if texto is None:
        return None
    digitos = _NO_DIGITOS.sub("", str(texto))
    if not digitos:
        return None
    if len(digitos) == 12:
        digitos = "0" + digitos
    elif len(digitos) == 8 and digitos[0] in "01" and not es_valido(digitos):
        # Un código de 8 dígitos se toma como EAN-8 (así lo guarda Open Food Facts); solo si no
        # valida como EAN-8 se prueba como UPC-E y se expande a UPC-A → EAN-13.
        upca = expandir_upce(digitos)
        if upca is not None and es_valido(upca):
            digitos = "0" + upca
    elif len(digitos) < 8:
        return None
    elif len(digitos) > 13:
        # GTIN-14 con indicador 0 → EAN-13 (p. ej. "07501055300075").
        if len(digitos) == 14 and digitos[0] == "0":
            digitos = digitos[1:]
        else:
            return None
    if len(digitos) not in (8, 13):
        return None
    if not es_valido(digitos):
        return None
    return digitos


def clave_fragmento(codigo: str) -> str:
    """Clave del fragmento (shard) de `api/v1/`: los últimos 3 dígitos del código normalizado."""
    return codigo[-3:]
