from datetime import date

from rest_framework.exceptions import ValidationError

from facturas.modelos import Factura


def _parse_date_param(name: str, value: str) -> date:
    try:
        return date.fromisoformat(value)  # YYYY-MM-DD
    except ValueError:
        raise ValidationError({name: f"Formato inválido para {name}. Use YYYY-MM-DD."})


def obtener_facturas_filtradas(params):
    qs = Factura.objects.select_related("cliente").all().order_by("-creado_en")

    cliente_id = params.get("cliente_id")
    if cliente_id:
        qs = qs.filter(cliente_id=cliente_id)

    estado = params.get("estado")
    if estado:
        qs = qs.filter(estado=estado)

    rut_deudor = params.get("rut_deudor")
    if rut_deudor:
        qs = qs.filter(rut_deudor=rut_deudor)

    fecha_desde = params.get("fecha_desde")
    if fecha_desde:
        qs = qs.filter(fecha_emision__gte=_parse_date_param("fecha_desde", fecha_desde))

    fecha_hasta = params.get("fecha_hasta")
    if fecha_hasta:
        qs = qs.filter(fecha_emision__lte=_parse_date_param("fecha_hasta", fecha_hasta))

    return qs
