from decimal import Decimal
from django.conf import settings
from rest_framework.exceptions import ValidationError
from clientes.modelos import EstadoCliente
from facturas.modelos import EstadoFactura
from operaciones.modelos.operacion_cesion import EstadoOperacion

def validar_cliente_activo(cliente):
    if cliente.estado != EstadoCliente.ACTIVO:
        raise ValidationError({"cliente": "El cliente debe estar en estado ACTIVO para cursar operaciones."})

def validar_facturas_ids(facturas_ids: list[int]):
    if not facturas_ids:
        raise ValidationError({"facturas_ids": "Debe seleccionar al menos una factura."})
    if len(facturas_ids) != len(set(facturas_ids)):
        raise ValidationError({"facturas_ids": "No se permiten facturas duplicadas."})

def validar_facturas_existen(facturas, facturas_ids):
    if len(facturas) != len(set(facturas_ids)):
        raise ValidationError({"facturas_ids": "Una o más facturas no existen."})

def validar_facturas_mismo_cliente(facturas, cliente_id):
    if any(f.cliente_id != cliente_id for f in facturas):
        raise ValidationError({"facturas_ids": "Todas las facturas deben pertenecer al mismo cliente."})

def validar_facturas_disponibles(facturas):
    no_disponibles = [f.id for f in facturas if f.estado != EstadoFactura.DISPONIBLE]
    if no_disponibles:
        raise ValidationError({"facturas_ids": f"Facturas no disponibles: {no_disponibles}."})

def validar_facturas_no_vencidas(facturas, hoy):
    vencidas = [f.id for f in facturas if f.fecha_vencimiento < hoy]
    if vencidas:
        raise ValidationError({"facturas_ids": f"No se pueden incluir facturas vencidas: {vencidas}."})

def validar_monto_total_positivo(monto_total: Decimal):
    if monto_total <= Decimal("0.00"):
        raise ValidationError({"facturas_ids": "El monto total de las facturas debe ser mayor a 0."})

def obtener_tasa(tasa_descuento):
    tasa = settings.DEFAULT_TASA_DESCUENTO if tasa_descuento is None else Decimal(tasa_descuento)
    if tasa <= 0 or tasa > Decimal("100"):
        raise ValidationError({"tasa_descuento": "La tasa de descuento debe estar entre 0 y 100."})
    return tasa

def validar_operacion_pendiente_para_aprobar(operacion):
    if operacion.estado != EstadoOperacion.PENDIENTE:
        raise ValidationError({"estado": "Solo se puede aprobar una operación en estado pendiente."})

def validar_operacion_pendiente_para_rechazar(operacion):
    if operacion.estado != EstadoOperacion.PENDIENTE:
        raise ValidationError({"estado": "Solo se puede rechazar una operación en estado pendiente."})

def validar_motivo_rechazo(motivo: str) -> str:
    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo_rechazo": "Debe indicar un motivo de rechazo."})
    return motivo

def validar_operacion_aprobada_para_desembolsar(operacion):
    if operacion.estado != EstadoOperacion.APROBADA:
        raise ValidationError({"estado": "Solo se puede desembolsar una operación aprobada."})

def validar_operacion_estado_para_finalizar(operacion):
    if operacion.estado not in (EstadoOperacion.APROBADA, EstadoOperacion.DESEMBOLSADA):
        raise ValidationError({"estado": "Solo se puede finalizar una operación aprobada o desembolsada."})

def validar_operacion_tiene_facturas(facturas):
    if not facturas:
        raise ValidationError({"facturas": "La operación no tiene facturas asociadas."})

def validar_facturas_siguen_disponibles_para_aprobar(facturas, hoy):
    if any(f.estado != EstadoFactura.DISPONIBLE for f in facturas):
        raise ValidationError({"facturas": "La operación contiene facturas que ya no están disponibles."})
    if any(f.fecha_vencimiento < hoy for f in facturas):
        raise ValidationError({"facturas": "La operación contiene facturas vencidas."})

def validar_facturas_pagadas_para_finalizar(facturas):
    if any(f.estado != EstadoFactura.PAGADA for f in facturas):
        raise ValidationError({"facturas": "No se puede finalizar: no todas las facturas están pagadas."})

def validar_linea_disponible_suficiente(cliente, monto_operacion):
    if monto_operacion > cliente.linea_disponible:
        raise ValidationError({"linea_disponible": "El monto excede la línea disponible del cliente."})

def validar_monto_operacion_positivo(monto):
    if monto <= Decimal("0.00"):
        raise ValidationError({"monto_total_facturas": "El monto total de la operación debe ser mayor a 0."})
