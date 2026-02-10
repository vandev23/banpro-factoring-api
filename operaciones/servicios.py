import logging
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from clientes.modelos import Cliente
from facturas.modelos import Factura
from facturas.modelos.factura import EstadoFactura
from operaciones.modelos import OperacionCesion, OperacionFactura, EstadoOperacion, TipoEventoOperacion
from operaciones.dominio.calculos import calcular_descuento
from operaciones.dominio.eventos import registrar_evento
from operaciones.dominio.validaciones import (
    validar_cliente_activo,
    validar_facturas_ids,
    validar_facturas_existen,
    validar_facturas_mismo_cliente,
    validar_facturas_disponibles,
    validar_facturas_no_vencidas,
    validar_facturas_pagadas_para_finalizar,
    validar_facturas_siguen_disponibles_para_aprobar,
    validar_linea_disponible_suficiente,
    validar_monto_total_positivo,
    obtener_tasa,
    validar_motivo_rechazo,
    validar_operacion_aprobada_para_desembolsar,
    validar_operacion_estado_para_finalizar,
    validar_operacion_pendiente_para_aprobar,
    validar_operacion_pendiente_para_rechazar,
    validar_operacion_tiene_facturas,
)

logger = logging.getLogger(__name__)


def _hoy() -> date:
    return timezone.localdate()


@transaction.atomic
def crear_operacion(cliente_id: int, facturas_ids: list[int], tasa_descuento: Decimal | None = None) -> OperacionCesion:
    validar_facturas_ids(facturas_ids)

    cliente = Cliente.objects.select_for_update().get(id=cliente_id)
    validar_cliente_activo(cliente)

    facturas = list(
        Factura.objects.select_for_update()
        .filter(id__in=facturas_ids)
        .select_related("cliente")
    )

    validar_facturas_existen(facturas, facturas_ids)
    validar_facturas_mismo_cliente(facturas, cliente.id)
    validar_facturas_disponibles(facturas)

    hoy = _hoy()
    validar_facturas_no_vencidas(facturas, hoy)

    monto_total = sum((f.monto_total for f in facturas), Decimal("0.00"))
    validar_monto_total_positivo(monto_total)

    tasa = obtener_tasa(tasa_descuento)

    venc_mas_lejano = max(f.fecha_vencimiento for f in facturas)
    dias = (venc_mas_lejano - hoy).days

    monto_desc, monto_desemb = calcular_descuento(monto_total, tasa, dias)

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

    registrar_evento(
        operacion=operacion,
        tipo=TipoEventoOperacion.CREADA,
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

    validar_operacion_pendiente_para_aprobar(operacion)

    # Lock cliente (consistencia línea)
    cliente = Cliente.objects.select_for_update().get(id=operacion.cliente_id)

    facturas = list(Factura.objects.select_for_update().filter(operaciones=operacion))
    validar_operacion_tiene_facturas(facturas)

    hoy = _hoy()
    validar_facturas_siguen_disponibles_para_aprobar(facturas, hoy)

    validar_linea_disponible_suficiente(cliente, operacion.monto_total_facturas)

    facturas_ids = [f.id for f in facturas]

    # Actualizar facturas -> cedida
    Factura.objects.filter(id__in=facturas_ids).update(estado=EstadoFactura.CEDIDA)

    # Actualizar línea disponible
    linea_anterior = cliente.linea_disponible
    cliente.linea_disponible = (cliente.linea_disponible - operacion.monto_total_facturas).quantize(Decimal("0.01"))
    cliente.save(update_fields=["linea_disponible", "actualizado_en"])

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.APROBADA
    operacion.fecha_aprobacion = timezone.now()
    operacion.motivo_rechazo = ""
    operacion.save(update_fields=["estado", "fecha_aprobacion", "motivo_rechazo", "actualizado_en"])

    registrar_evento(
        operacion=operacion,
        tipo=TipoEventoOperacion.APROBADA,
        estado_anterior=estado_anterior,
        estado_nuevo=operacion.estado,
        detalle={
            "linea_disponible_anterior": str(linea_anterior.quantize(Decimal("0.01"))),
            "linea_disponible_nueva": str(cliente.linea_disponible),
            "facturas_ids": facturas_ids,
        },
    )

    logger.info("Operación aprobada", extra={"operacion_id": operacion.id, "cliente_id": cliente.id})
    return operacion


@transaction.atomic
def rechazar_operacion(operacion_id: int, motivo: str) -> OperacionCesion:
    operacion = OperacionCesion.objects.select_for_update().get(id=operacion_id)

    validar_operacion_pendiente_para_rechazar(operacion)
    motivo = validar_motivo_rechazo(motivo)

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.RECHAZADA
    operacion.motivo_rechazo = motivo
    operacion.fecha_aprobacion = None
    operacion.save(update_fields=["estado", "motivo_rechazo", "fecha_aprobacion", "actualizado_en"])

    registrar_evento(
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

    validar_operacion_aprobada_para_desembolsar(operacion)

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.DESEMBOLSADA
    operacion.fecha_desembolso = timezone.now()
    operacion.save(update_fields=["estado", "fecha_desembolso", "actualizado_en"])

    registrar_evento(
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
    operacion = OperacionCesion.objects.select_for_update().select_related("cliente").get(id=operacion_id)

    validar_operacion_estado_para_finalizar(operacion)

    # Lock cliente para restaurar línea
    cliente = Cliente.objects.select_for_update().get(id=operacion.cliente_id)

    facturas = list(Factura.objects.select_for_update().filter(operaciones=operacion))
    validar_operacion_tiene_facturas(facturas)
    validar_facturas_pagadas_para_finalizar(facturas)

    linea_anterior = cliente.linea_disponible
    cliente.linea_disponible = (cliente.linea_disponible + operacion.monto_total_facturas).quantize(Decimal("0.01"))
    cliente.save(update_fields=["linea_disponible", "actualizado_en"])

    estado_anterior = operacion.estado
    operacion.estado = EstadoOperacion.FINALIZADA
    operacion.fecha_finalizacion = timezone.now()
    operacion.save(update_fields=["estado", "fecha_finalizacion", "actualizado_en"])

    registrar_evento(
        operacion=operacion,
        tipo=TipoEventoOperacion.FINALIZADA,
        estado_anterior=estado_anterior,
        estado_nuevo=operacion.estado,
        detalle={
            "linea_disponible_anterior": str(linea_anterior.quantize(Decimal("0.01"))),
            "linea_disponible_nueva": str(cliente.linea_disponible),
        },
    )

    logger.info("Operación finalizada", extra={"operacion_id": operacion.id, "cliente_id": cliente.id})
    return operacion