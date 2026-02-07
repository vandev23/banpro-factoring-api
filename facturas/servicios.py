from django.utils import timezone

from facturas.modelos import Factura, EstadoFactura


def marcar_pagada(factura: Factura) -> Factura:
    factura.estado = EstadoFactura.PAGADA
    factura.save(update_fields=["estado", "actualizado_en"])
    return factura


def marcar_anulada(factura: Factura) -> Factura:
    factura.estado = EstadoFactura.ANULADA
    factura.save(update_fields=["estado", "actualizado_en"])
    return factura
