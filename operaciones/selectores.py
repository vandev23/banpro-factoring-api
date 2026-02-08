from datetime import date
from rest_framework.exceptions import ValidationError

from operaciones.modelos import OperacionCesion


def _parse_date(name: str, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({name: f"Formato inválido para {name}. Use YYYY-MM-DD."})


def obtener_operaciones_filtradas(params):
    qs = OperacionCesion.objects.select_related("cliente").all().order_by("-fecha_solicitud")

    cliente_id = params.get("cliente_id")
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)

    estado = params.get("estado")
    if estado:
        qs = qs.filter(estado=estado)

    fecha_desde = params.get("fecha_desde")
    if fecha_desde:
        qs = qs.filter(fecha_solicitud__date__gte=_parse_date("fecha_desde", fecha_desde))

    fecha_hasta = params.get("fecha_hasta")
    if fecha_hasta:
        qs = qs.filter(fecha_solicitud__date__lte=_parse_date("fecha_hasta", fecha_hasta))

    return qs
