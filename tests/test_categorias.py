import pytest

from catalogo import categorias


@pytest.mark.parametrize("etiquetas, esperado", [
    (["en:beverages", "en:carbonated-drinks", "en:sodas", "en:colas"], "Bebidas"),
    (["en:beverages", "en:dairies", "en:milks"], "Lácteos"),
    (["en:snacks", "en:salty-snacks", "en:appetizers", "en:chips-and-fries", "en:crisps"], "Botanas"),
    (["en:snacks", "en:sweet-snacks", "en:biscuits-and-cakes", "en:biscuits"], "Panadería"),
    (["en:breads", "en:sliced-breads"], "Panadería"),
    (["en:snacks", "en:sweet-snacks", "en:confectioneries", "en:candies"], "Dulces"),
    (["en:snacks", "en:sweet-snacks", "en:cocoa-and-its-products", "en:chocolates"], "Dulces"),
    (["en:breakfasts", "en:cereals-and-potatoes", "en:breakfast-cereals", "en:chocolate-cereals"], "Abarrotes"),
    (["en:spreads", "en:sweet-spreads", "en:chocolate-spreads"], "Abarrotes"),
    (["en:canned-foods", "en:canned-vegetables"], "Enlatados"),
    (["en:seafood", "en:fishes", "en:canned-fishes", "en:canned-tunas"], "Enlatados"),
    (["en:frozen-foods", "en:desserts", "en:frozen-desserts", "en:ice-creams"], "Congelados"),
    (["en:meats", "en:prepared-meats", "en:sausages"], "Carnes y embutidos"),
    (["en:dog-and-cat-food", "en:cat-food"], "Mascotas"),
    (["en:baby-foods", "en:infant-formulas"], "Bebés"),
    (["en:cleaning", "en:laundry-detergents"], "Limpieza"),
    (["en:hygiene", "en:shampoos"], "Higiene personal"),
    (["en:condiments", "en:sauces", "en:hot-sauces"], "Abarrotes"),
    (["en:plant-based-foods-and-beverages", "en:plant-based-foods", "en:legumes", "en:beans"], "Abarrotes"),
    (["en:dairies", "en:cheeses"], "Lácteos"),
    (["en:eggs"], "Lácteos"),
    (["en:beverages", "en:alcoholic-beverages", "en:beers"], "Bebidas"),
    (["en:tortillas"], "Panadería"),
    (["en:foods"], "Abarrotes"),
    ([], "Otros"),
    (None, "Otros"),
])
def test_categoria_para(etiquetas, esperado):
    assert categorias.categoria_para(etiquetas) == esperado


def test_valor_por_defecto_segun_fuente():
    assert categorias.categoria_para([], "obf") == "Higiene personal"
    assert categorias.categoria_para([], "opff") == "Mascotas"
    assert categorias.categoria_para([], "opf") == "Otros"
    assert categorias.categoria_para(["es:vitaminas-y-suplementos"], "opf") == "Higiene personal"


def test_todas_las_reglas_usan_categorias_conocidas():
    for categoria, _ in categorias.REGLAS:
        assert categoria in categorias.CATEGORIAS


@pytest.mark.parametrize("nombre, esperado", [
    ("Coca-Cola", "Bebidas"),
    ("Papas Sabritas sabor limón", "Botanas"),
    ("Leche entera Lala 1 L", "Lácteos"),
    ("Galletas Marías Gamesa", "Panadería"),
    ("Pan Blanco Grande", "Panadería"),
    ("Atún en agua", "Enlatados"),
    ("Salsa Valentina", "Abarrotes"),
    ("Jabón Zote", "Higiene personal"),
    ("Papel higiénico Pétalo", "Higiene personal"),
    ("Detergente Ariel", "Limpieza"),
    ("Croquetas para perro adulto", "Mascotas"),
    ("Pañales etapa 3", "Bebés"),
    ("Helado de vainilla", "Congelados"),
    ("Paleta helada de mango", "Congelados"),
    ("Paleta de caramelo", "Dulces"),
    ("Leche con chocolate", "Lácteos"),
    ("Salchicha de pavo", "Carnes y embutidos"),
    ("Producto desconocido", None),
    ("", None),
    (None, None),
])
def test_categoria_por_nombre(nombre, esperado):
    assert categorias.categoria_por_nombre(nombre) == esperado


def test_nombre_solo_decide_si_las_etiquetas_no():
    assert categorias.categoria_para(["en:sodas"], "off", "Leche") == "Bebidas"
    assert categorias.categoria_para([], "off", "Leche Lala") == "Lácteos"
    assert categorias.categoria_para(["en:foods"], "off", "Leche Lala") == "Lácteos"
    assert categorias.categoria_para(["en:snacks", "en:salty-snacks", "en:sweet-snacks", "en:salted-popcorn"]) == "Botanas"
