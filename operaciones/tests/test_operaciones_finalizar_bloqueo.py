import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def _cliente():
    return Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa",
        email="a@a.cl",
        linea_credito="300000.00",
        linea_disponible="300000.00",
        estado=EstadoCliente.ACTIVO,
    )


def _factura(cliente, numero, monto):
    hoy = timezone.localdate()
    return Factura.objects.create(
        cliente=cliente,
        numero_factura=numero,
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=Decimal(monto),
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=30),
        estado=EstadoFactura.DISPONIBLE,
    )


def test_no_finaliza_si_no_todas_pagadas():
    api = APIClient()
    c = _cliente()
    f1 = _factura(c, "F-1", "100000.00")
    f2 = _factura(c, "F-2", "50000.00")

    op_id = api.post("/api/operaciones/", {"cliente": c.id, "facturas_ids": [f1.id, f2.id]}, format="json").json()["id"]
    api.post(f"/api/operaciones/{op_id}/aprobar/")

    # pagamos solo una
    api.post(f"/api/facturas/{f1.id}/pagar/")

    r_final = api.post(f"/api/operaciones/{op_id}/finalizar/")
    assert r_final.status_code == 400
