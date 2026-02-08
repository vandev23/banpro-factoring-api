import logging
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from clientes.modelos import Cliente
from facturas.modelos import Factura, EstadoFactura
from operaciones.modelos import OperacionCesion, OperacionFactura, EstadoOperacion
from operaciones.modelos import OperacionEvento, TipoEventoOperacion
from core.request_context import request_id_ctx

logger = logging.getLogger(__name__)


def _hoy() -> date:
    return timezone.localdate()


def _registrar_evento(
    *,
    operacion: OperacionCesion,
    tipo: str,
    estado_anterior: str = "",
    estado_nuevo: str = "",
    detalle: dict | None = None,
):
    payload = detalle.copy() if detalle else {}
    payload["request_id"] = request_id_ctx.get()

    OperacionEvento.objects.create(
        operacion=operacion,
        tipo=tipo,
        estado_anterior=estado_anterior or "",
        estado_nuevo=estado_nuevo or "",
        detalle=payload,
    )


def _calcular_descuento(monto_total: Decimal, tasa: Decimal, dias_hasta_venc: int) -> tuple[Decimal, Decimal]:
    # monto_descuento = monto_total * (tasa/100) * (dias/360)
    monto_desc = (monto_total * (tasa / Decimal("100")) * (Decimal(dias_hasta_venc) / Decimal("360")))
    monto_desc = monto_desc.quantize(Decimal("0.01"))
    monto_desemb = (monto_total - monto_desc).quantize(Decimal("0.01"))
    return monto_desc, monto_desemb


@transaction.atomic
def crear_operacion(cliente_id: int, facturas_ids: list[int], tasa_descuento: Decimal | None = None) -> OperacionCesion:
    if not facturas_ids:
        raise ValidationError({"facturas_ids": "Debe seleccionar al menos una factura."})

    cliente = Cliente.objects.select_for_update().get(id=cliente_id)

    facturas = list(
        Factura.objects.select_for_update()
        .filter(id__in=facturas_ids)
        .select_related("cliente")
    )

    if len(facturas) != len(set(facturas_ids)):
        raise ValidationError({"facturas_ids": "Una o más facturas no existen."})

    # Validar que pertenecen al mismo cliente
    if any(f.cliente_id != cliente.id for f in facturas):
        raise ValidationError({"facturas_ids": "Todas las facturas deben pertenecer al mismo cliente."})

    # Validar estado disponible
    no_disponibles = [f.id for f in facturas if f.estado != EstadoFactura.DISPONIBLE]
    if no_disponibles:
        raise ValidationError({"facturas_ids": f"Facturas no disponibles: {no_disponibles}."})

    # Validar no vencidas (fecha_vencimiento >= hoy)
    hoy = _hoy()
    vencidas = [f.id for f in facturas if f.fecha_vencimiento < hoy]
    if vencidas:
        raise ValidationError({"facturas_ids": f"No se pueden incluir facturas vencidas: {vencidas}."})

    monto_total = sum((f.monto_total for f in facturas), Decimal("0.00"))

    # tasa
    tasa = Decimal(tasa_descuento) if tasa_descuento is not None else Decimal("2.00")

    # vencimiento más lejano
    venc_mas_lejano = max(f.fecha_vencimiento for f in facturas)
    dias = (venc_mas_lejano - hoy).days
    if dias < 0:
        raise ValidationError({"facturas_ids": "No se pueden incluir facturas ya vencidas."})

    monto_desc, monto_desemb = _calcular_descuento(monto_total, tasa, dias)

    operacion = OperacionCesion.objects.create(
        cliente=cliente,
        fecha_solicitud=timezone.now(),
        tasa_descuento=tasa,
        monto_total_facturas=monto_total,
        monto_descuento=monto_desc,
        monto_a_desembolsar=monto_desemb,
        estado=EstadoOperacion.PENDIENTE,
    )

    OperacionFactura.objects.bulk_create(
        [OperacionFactura(operacion=operacion, factura=f) for f in facturas]
    )

    _registrar_evento(
    operacion=operacion,
    tipo=TipoEventoOperacion.CREADA,
    estado_anterior="",
    estado_nuevo=operacion.estado,
    detalle={
        "facturas_ids": facturas_ids,
        "monto_total_facturas": str(monto_total),
        "tasa_descuento": str(tasa),
        "monto_descuento": str(monto_desc),
        "monto_a_desembolsar": str(monto_desemb),
    },
    )

    logger.info("Operación creada", extra={"operacion_id": operacion.id, "cliente_id": cliente.id})
    return operacion


@transaction.atomic
def aprobar_operacion(operacion_id: int) -> OperacionCesion:
    operacion = (
        OperacionCesion.objects.select_for_update()
        .select_related("cliente")
        .get(id=operacion_id)
    )
    cliente = Cliente.objects.select_for_update().get(id=operacion.cliente_id)

    if operacion.estado != EstadoOperacion.PENDIENTE:
        raise ValidationError({"estado": "Solo se puede aprobar una operación en estado pendiente."})

    facturas = list(
        Factura.objects.select_for_update()
        .filter(operaciones=operacion)
    )

    # Revalidar estado disponible y no vencidas (por si cambiaron)
    hoy = _hoy()
    if any(f.estado != EstadoFactura.DISPONIBLE for f in facturas):
        raise ValidationError({"facturas": "La operación contiene facturas que ya no están disponibles."})
    if any(f.fecha_vencimiento < hoy for f in facturas):
        raise ValidationError({"facturas": "La operación contiene facturas vencidas."})

    # Regla: no exceder línea disponible
    if operacion.monto_total_facturas > cliente.linea_disponible:
        raise ValidationError({"linea_disponible": "El monto excede la línea disponible del cliente."})

    # Actualizar facturas -> cedida
    Factura.objects.filter(id__in=[f.id for f in facturas]).update(estado=EstadoFactura.CEDIDA)

    # Actualizar línea disponible
    cliente.linea_disponible = (cliente.linea_disponible - operacion.monto_total_facturas).quantize(Decimal("0.01"))
    cliente.save(update_fields=["linea_disponible", "actualizado_en"])

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.APROBADA
    operacion.fecha_aprobacion = timezone.now()
    operacion.motivo_rechazo = ""
    operacion.save(update_fields=["estado", "fecha_aprobacion", "motivo_rechazo", "actualizado_en"])

    _registrar_evento(
    operacion=operacion,
    tipo=TipoEventoOperacion.APROBADA,
    estado_anterior=estado_anterior,
    estado_nuevo=operacion.estado,
    detalle={
        "linea_disponible_anterior": str((cliente.linea_disponible + operacion.monto_total_facturas).quantize(Decimal("0.01"))),
        "linea_disponible_nueva": str(cliente.linea_disponible),
        "facturas": [f.id for f in facturas],
    },
    )

    logger.info("Operación aprobada", extra={"operacion_id": operacion.id, "cliente_id": cliente.id})
    return operacion


@transaction.atomic
def rechazar_operacion(operacion_id: int, motivo: str) -> OperacionCesion:
    operacion = OperacionCesion.objects.select_for_update().get(id=operacion_id)

    if operacion.estado != EstadoOperacion.PENDIENTE:
        raise ValidationError({"estado": "Solo se puede rechazar una operación en estado pendiente."})

    motivo = (motivo or "").strip()
    if not motivo:
        raise ValidationError({"motivo_rechazo": "Debe indicar un motivo de rechazo."})

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.RECHAZADA
    operacion.motivo_rechazo = motivo
    operacion.fecha_aprobacion = None
    operacion.save(update_fields=["estado", "motivo_rechazo", "fecha_aprobacion", "actualizado_en"])

    _registrar_evento(
    operacion=operacion,
    tipo=TipoEventoOperacion.RECHAZADA,
    estado_anterior=estado_anterior,
    estado_nuevo=operacion.estado,
    detalle={"motivo_rechazo": motivo},
    )
    
    logger.info("Operación rechazada", extra={"operacion_id": operacion.id})
    return operacion


@transaction.atomic
def registrar_desembolso(operacion_id: int) -> OperacionCesion:
    operacion = OperacionCesion.objects.select_for_update().get(id=operacion_id)

    if operacion.estado != EstadoOperacion.APROBADA:
        raise ValidationError({"estado": "Solo se puede desembolsar una operación aprobada."})

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.DESEMBOLSADA
    operacion.fecha_desembolso = timezone.now()
    operacion.save(update_fields=["estado", "fecha_desembolso", "actualizado_en"])

    _registrar_evento(
    operacion=operacion,
    tipo=TipoEventoOperacion.DESEMBOLSADA,
    estado_anterior=estado_anterior,
    estado_nuevo=operacion.estado,
    detalle={"monto_a_desembolsar": str(operacion.monto_a_desembolsar)},
    )

    logger.info("Desembolso registrado", extra={"operacion_id": operacion.id})
    return operacion


@transaction.atomic
def finalizar_operacion_si_pagada(operacion_id: int) -> OperacionCesion:
    """
    Simplificación: finalizamos cuando TODAS las facturas de la operación están en estado PAGADA.
    Al finalizar, restauramos la línea disponible del cliente (regla del enunciado).
    """
    operacion = OperacionCesion.objects.select_for_update().select_related("cliente").get(id=operacion_id)
    cliente = Cliente.objects.select_for_update().get(id=operacion.cliente_id)

    if operacion.estado not in (EstadoOperacion.APROBADA, EstadoOperacion.DESEMBOLSADA):
        raise ValidationError({"estado": "Solo se puede finalizar una operación aprobada o desembolsada."})

    facturas = list(Factura.objects.select_for_update().filter(operaciones=operacion))
    if not facturas:
        raise ValidationError({"facturas": "La operación no tiene facturas asociadas."})

    if any(f.estado != EstadoFactura.PAGADA for f in facturas):
        raise ValidationError({"facturas": "No se puede finalizar: no todas las facturas están pagadas."})

    # Restaurar línea
    cliente.linea_disponible = (cliente.linea_disponible + operacion.monto_total_facturas).quantize(Decimal("0.01"))
    cliente.save(update_fields=["linea_disponible", "actualizado_en"])

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.FINALIZADA
    operacion.fecha_finalizacion = timezone.now()
    operacion.save(update_fields=["estado", "fecha_finalizacion", "actualizado_en"])

    _registrar_evento(
    operacion=operacion,
    tipo=TipoEventoOperacion.FINALIZADA,
    estado_anterior=estado_anterior,
    estado_nuevo=operacion.estado,
    detalle={"linea_disponible_nueva": str(cliente.linea_disponible)},
    )

    logger.info("Operación finalizada", extra={"operacion_id": operacion.id})
    return operacion
