import re

_RUT_RE = re.compile(r"^(\d{1,2})\.?(\d{3})\.?(\d{3})-([\dkK])$")


def normalizar_rut(rut: str) -> str:
    rut = rut.strip().replace(" ", "").upper()
    rut = rut.replace("‐", "-").replace("–", "-").replace("—", "-")

    m = _RUT_RE.match(rut)
    if m:
        return f"{m.group(1)}.{m.group(2)}.{m.group(3)}-{m.group(4).upper()}"

    rut_limpio = rut.replace(".", "")
    m2 = re.match(r"^(\d{7,8})-([\dkK])$", rut_limpio)
    if not m2:
        raise ValueError("RUT con formato inválido")

    num = m2.group(1).zfill(8)
    dv = m2.group(2).upper()
    return f"{num[0:2]}.{num[2:5]}.{num[5:8]}-{dv}"


def _dv_rut(numero: str) -> str:
    factores = [2, 3, 4, 5, 6, 7]
    s = 0
    for i, d in enumerate(map(int, reversed(numero))):
        s += d * factores[i % len(factores)]
    mod = 11 - (s % 11)
    if mod == 11:
        return "0"
    if mod == 10:
        return "K"
    return str(mod)


def es_rut_valido(rut: str) -> bool:
    try:
        formateado = normalizar_rut(rut)
    except ValueError:
        return False

    sin_puntos = formateado.replace(".", "")
    numero, dv = sin_puntos.split("-")
    return _dv_rut(numero) == dv.upper()
