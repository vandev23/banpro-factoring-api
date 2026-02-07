from decimal import Decimal, InvalidOperation

from rest_framework.exceptions import ValidationError

from clientes.modelos import Cliente


def _parse_decimal_param(name: str, value: str) -> Decimal:
    try:
        dec = Decimal(value)
    except (InvalidOperation, ValueError):
        raise ValidationError({name: f"Valor inválido para {name}: '{value}' (debe ser numérico)."})
    if dec < 0:
        raise ValidationError({name: f"{name} no puede ser negativo."})
    return dec


def obtener_clientes_filtrados(params):
    """
    params: request.query_params (QueryDict)
    """
    qs = Cliente.objects.all().order_by("-creado_en")

    # 1) estado
    estado = params.get("estado")
    if estado:
        qs = qs.filter(estado=estado)

    # 2) rangos línea de crédito
    linea_min_raw = params.get("linea_credito_min")
    linea_max_raw = params.get("linea_credito_max")

    dec_min = None
    dec_max = None

    if linea_min_raw is not None and linea_min_raw != "":
        dec_min = _parse_decimal_param("linea_credito_min", linea_min_raw)
        qs = qs.filter(linea_credito__gte=dec_min)

    if linea_max_raw is not None and linea_max_raw != "":
        dec_max = _parse_decimal_param("linea_credito_max", linea_max_raw)
        qs = qs.filter(linea_credito__lte=dec_max)

    if dec_min is not None and dec_max is not None and dec_min > dec_max:
        raise ValidationError({"linea_credito": "linea_credito_min no puede ser mayor que linea_credito_max."})

    # 3) búsqueda opcional
    q = params.get("q")
    if q:
        qs = qs.filter(razon_social__icontains=q) | qs.filter(rut__icontains=q)

    return qs
