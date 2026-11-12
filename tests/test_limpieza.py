import pytest

from catalogo import limpieza


@pytest.mark.parametrize("texto, esperado", [
    ("600 ml", (600, "ml")),
    ("355ml", (355, "ml")),
    ("1,5 L", (1.5, "l")),
    ("1.5 Litros", (1.5, "l")),
    ("1 kg", (1, "kg")),
    ("500 g", (500, "g")),
    ("500 gr.", (500, "g")),
    ("6 x 355 ml", (2130, "ml")),
    ("12 piezas", (12, "pz")),
    ("2 pzas", (2, "pz")),
    ("16 oz", (16, "oz")),
    ("12 fl oz", (12, "fl oz")),
    ("", (None, None)),
    (None, (None, None)),
    ("Paquete familiar", (None, None)),
    ("200", (200, None)),
    ("60 gomitas de 2.8g c/u", (2.8, "g")),
    ("6.5 FL OZ (190ml)", (190, "ml")),
    ("1 kg (2.2 lb)", (1, "kg")),
])
def test_analizar_cantidad(texto, esperado):
    assert limpieza.analizar_cantidad(texto) == esperado


def test_cantidad_desde_off_usa_campos_normalizados_si_falta_unidad():
    assert limpieza.cantidad_desde_off("Paquete familiar", "500", "g") == (500, "g")
    assert limpieza.cantidad_desde_off("600 ml", "600", "ml") == (600, "ml")
    assert limpieza.cantidad_desde_off("", None, None) == (None, None)


def test_limpiar_nombre():
    assert limpieza.limpiar_nombre("  Coca-Cola   Original \n") == "Coca-Cola Original"
    assert limpieza.limpiar_nombre("PAN BLANCO GRANDE") == "Pan Blanco Grande"
    assert limpieza.limpiar_nombre("Sabritas") == "Sabritas"
    assert limpieza.limpiar_nombre(None) == ""
    assert limpieza.limpiar_nombre("LECHE DE VACA") == "Leche de Vaca"


def test_limpiar_marca():
    assert limpieza.limpiar_marca("Coca-Cola, The Coca-Cola Company") == "Coca-Cola"
    assert limpieza.limpiar_marca("  Lala ") == "Lala"
    assert limpieza.limpiar_marca("") == ""
