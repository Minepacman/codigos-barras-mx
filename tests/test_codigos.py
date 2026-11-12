import pytest

from catalogo import codigos


@pytest.mark.parametrize("codigo", ["7501055300075", "7501000111541", "4006381333931", "96385074", "0012345678905"])
def test_codigos_validos(codigo):
    assert codigos.es_valido(codigo)
    assert codigos.normalizar(codigo) == codigo


@pytest.mark.parametrize("codigo", ["7501055300076", "7501055300074", "96385075", "1234", "", "abc"])
def test_codigos_invalidos(codigo):
    assert codigos.normalizar(codigo) is None


def test_digito_control():
    assert codigos.digito_control("750105530007") == 5
    assert codigos.digito_control("9638507") == 4
    assert codigos.digito_control("012345678905"[:-1]) == 5


def test_upca_se_convierte_a_ean13():
    assert codigos.normalizar("012345678905") == "0012345678905"
    assert codigos.normalizar("036000291452") == "0036000291452"


def test_limpia_espacios_y_guiones():
    assert codigos.normalizar(" 750-1055-300075 ") == "7501055300075"
    assert codigos.normalizar("7 501 055 300 075") == "7501055300075"


def test_gtin14_con_indicador_cero():
    assert codigos.normalizar("07501055300075") == "7501055300075"
    assert codigos.normalizar("17501055300072") is None


def test_upce_se_expande():
    assert codigos.expandir_upce("04252614") == "042100005264"
    assert codigos.normalizar("04252614") == "0042100005264"


def test_ean8_valido_se_conserva_aunque_empiece_con_0_o_1():
    assert codigos.es_valido("01234565")
    assert codigos.normalizar("01234565") == "01234565"
    # 19028897 es EAN-8 válido y también expandiría como UPC-E: gana EAN-8 (como lo guarda OFF).
    assert codigos.normalizar("19028897") == "19028897"


def test_clave_fragmento():
    assert codigos.clave_fragmento("7501055300075") == "075"
    assert codigos.clave_fragmento("96385074") == "074"


def test_none():
    assert codigos.normalizar(None) is None
