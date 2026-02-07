import pytest

from core.rut import es_rut_valido, normalizar_rut


@pytest.mark.parametrize(
    "rut",
    [
        "12.345.678-5",
        "12345678-5",
        "12.345.678-5 ",
        " 12.345.678-5"
    ],
)
def test_es_rut_valido_true(rut):
    assert es_rut_valido(rut) is True


@pytest.mark.parametrize(
    "rut",
    [
        "12.345.678-0",      # DV incorrecto
        "12.345.678",        # sin DV
        "12.345.678-A",      # DV inválido
        "abc",               # no es ni cerca de un RUT
        "1.234.567-8-9",     # formato completamente inválido
    ],
)
def test_es_rut_valido_false(rut):
    assert es_rut_valido(rut) is False


def test_normalizar_rut_con_puntos():
    assert normalizar_rut("12345678-5") == "12.345.678-5"


def test_normalizar_rut_k_mayuscula():
    # Caso clásico: 12.345.678-K (si tu dv fuera K en algún rut)
    # Aquí no validamos el DV, solo normalizamos formato
    assert normalizar_rut("12345678-k").endswith("-K")


def test_normalizar_rut_formato_invalido_lanza_error():
    with pytest.raises(ValueError):
        normalizar_rut("rut-malo")
