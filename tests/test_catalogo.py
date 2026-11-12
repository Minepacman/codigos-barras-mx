import json

import pytest

from catalogo import catalogo, fuentes

CRUDO_COCA = {
    "code": "7501055300075", "lang": "es", "product_name": "Coca-Cola", "product_name_es": "Coca-Cola",
    "brands": "Coca-Cola, The Coca-Cola Company", "quantity": "355 ml", "product_quantity": "355",
    "product_quantity_unit": "ml",
    "categories_tags": ["en:beverages", "en:carbonated-drinks", "en:sodas", "en:colas"],
    "countries_tags": ["en:mexico"], "imagen": "https://images.openfoodfacts.org/x/front_es.1.200.jpg",
    "last_modified_t": 1773407240, "obsolete": False, "fuente": "off",
}


def test_convertir_crudo():
    fila = catalogo.convertir_crudo(CRUDO_COCA)
    assert fila == {
        "codigo": "7501055300075", "nombre": "Coca-Cola", "marca": "Coca-Cola", "cantidad": 355, "unidad": "ml",
        "contenido": "355 ml", "categoria": "Bebidas", "imagen": "https://images.openfoodfacts.org/x/front_es.1.200.jpg",
        "fuente": "off", "actualizado": "2026-03-13",
    }


def test_convertir_descarta_invalidos():
    assert catalogo.convertir_crudo({**CRUDO_COCA, "code": "7501055300076"}) is None
    assert catalogo.convertir_crudo({**CRUDO_COCA, "obsolete": True}) is None
    assert catalogo.convertir_crudo({**CRUDO_COCA, "product_name": "", "product_name_es": None}) is None


def test_prefiere_nombre_en_espanol():
    fila = catalogo.convertir_crudo({**CRUDO_COCA, "product_name": "Coke", "product_name_es": "Coca-Cola"})
    assert fila["nombre"] == "Coca-Cola"
    fila = catalogo.convertir_crudo({**CRUDO_COCA, "product_name": "Coke", "product_name_es": None})
    assert fila["nombre"] == "Coke"


MANUAL = """# comentario
codigo,nombre,marca,cantidad,unidad,contenido,categoria,imagen,fuente,actualizado
7501055300075,Coca-Cola 355 ml,Coca-Cola,355,ml,355 ml,Bebidas,,manual,2026-01-01
7501000111541,Pan Blanco Grande,Bimbo,680,g,680 g,Panadería,,,
"""


def test_leer_manual():
    filas = catalogo.leer_manual(MANUAL)
    assert [f["codigo"] for f in filas] == ["7501055300075", "7501000111541"]
    assert filas[0]["fuente"] == "manual" and filas[1]["fuente"] == "manual"
    assert filas[0]["cantidad"] == 355


def test_leer_manual_vacio_solo_encabezado():
    assert catalogo.leer_manual("codigo,nombre,marca,cantidad,unidad,contenido,categoria,imagen,fuente,actualizado\n") == []
    assert catalogo.leer_manual("") == []


@pytest.mark.parametrize("linea, mensaje", [
    ("7501055300076,Coca-Cola,Coca-Cola,,,,Bebidas,,,", "código inválido"),
    ("7501055300075,,Coca-Cola,,,,Bebidas,,,", "nombre"),
    ("7501055300075,Coca-Cola,Coca-Cola,,,,Refrescos,,,", "categoría"),
    ("7501055300075,Coca-Cola,Coca-Cola,abc,,,Bebidas,,,", "cantidad"),
    ("7501055300075,Coca-Cola,Coca-Cola,,,,Bebidas,,,12/01/2026", "fecha"),
    ("7501055300075,Coca-Cola,Coca-Cola,,,,Bebidas,,", "columnas"),
])
def test_leer_manual_errores(linea, mensaje):
    texto = "codigo,nombre,marca,cantidad,unidad,contenido,categoria,imagen,fuente,actualizado\n" + linea + "\n"
    with pytest.raises(catalogo.ErrorManual, match=mensaje):
        catalogo.leer_manual(texto)


def test_leer_manual_duplicado():
    texto = ("codigo,nombre,marca,cantidad,unidad,contenido,categoria,imagen,fuente,actualizado\n"
             "7501055300075,A,,,,,Bebidas,,,\n7501055300075,B,,,,,Bebidas,,,\n")
    with pytest.raises(catalogo.ErrorManual, match="repetido"):
        catalogo.leer_manual(texto)


def test_combinar_prioriza_manual_y_mas_reciente():
    off = catalogo.convertir_crudo(CRUDO_COCA)
    off_viejo = {**off, "nombre": "Vieja", "actualizado": "2020-01-01"}
    manual = catalogo.leer_manual(MANUAL)[0]
    assert catalogo.combinar([off_viejo, off])[0]["nombre"] == "Coca-Cola"
    assert catalogo.combinar([off, manual])[0]["nombre"] == "Coca-Cola 355 ml"
    assert catalogo.combinar([manual, off])[0]["fuente"] == "manual"


def test_csv_y_jsonl_y_fragmentos():
    filas = catalogo.combinar([catalogo.convertir_crudo(CRUDO_COCA)] + catalogo.leer_manual(MANUAL)[1:])
    csv_texto = catalogo.a_csv(filas)
    assert csv_texto.splitlines()[0] == ",".join(catalogo.COLUMNAS)
    assert len(csv_texto.splitlines()) == 3
    registros = [json.loads(l) for l in catalogo.a_jsonl(filas).splitlines()]
    assert registros[1]["codigo"] == "7501055300075" and registros[1]["cantidad"] == 355
    grupos = catalogo.fragmentos(filas)
    assert set(grupos) == {"075", "541"}
    assert grupos["075"]["7501055300075"]["nombre"] == "Coca-Cola"
    assert "codigo" not in grupos["075"]["7501055300075"]
    json.loads(catalogo.a_json_fragmento(grupos["075"]))


def test_url_imagen():
    assert fuentes.url_imagen("7501055300075", "es", [("front_fr", 25), ("front_es", 12)]) == \
        "https://images.openfoodfacts.org/images/products/750/105/530/0075/front_es.12.200.jpg"
    assert fuentes.url_imagen("7501055300075", "fr", [("front_fr", 25)]) == \
        "https://images.openfoodfacts.org/images/products/750/105/530/0075/front_fr.25.200.jpg"
    assert fuentes.url_imagen("96385074", "es", [("front_es", 3)], "obf") == \
        "https://images.openbeautyfacts.org/images/products/96385074/front_es.3.200.jpg"
    assert fuentes.url_imagen("7501055300075", "es", []) == ""
    assert fuentes.url_imagen("7501055300075", "es", [("ingredients_es", 1)]) == ""


def test_fecha_iso():
    assert catalogo.fecha_iso(1773407240) == "2026-03-13"
    assert catalogo.fecha_iso(None) == ""
    assert catalogo.fecha_iso("x") == ""
