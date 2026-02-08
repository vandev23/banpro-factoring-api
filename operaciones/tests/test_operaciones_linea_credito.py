import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def _crear_cliente(credito="100000.00", disponible="100000.00"):
    return Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa Demo",
        email="demo@empresa.cl",
        linea_credito=credito,
        linea_disponible=disponible,
        estado=EstadoCliente.ACTIVO,
    )


def _crear_factura(cliente, numero, monto, dias_hasta_venc=30):
    hoy = timezone.localdate()
    return Factura.objects.create(
        cliente=cliente,
        numero_factura=numero,
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=monto,
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=dias_hasta_venc),
        estado=EstadoFactura.DISPONIBLE,
    )


def test_aprobar_operacion_falla_si_excede_linea_disponible():
    api = APIClient()
    cliente = _crear_cliente(credito="100000.00", disponible="100000.00")

    # Total facturas 150k > 100k disponible
    f1 = _crear_factura(cliente, "F-1", Decimal("100000.00"))
    f2 = _crear_factura(cliente, "F-2", Decimal("50000.00"))

    r_create = api.post(
        "/api/operaciones/",
        {"cliente": cliente.id, "facturas_ids": [f1.id, f2.id], "tasa_descuento": "2.00"},
        format="json",
    )
    assert r_create.status_code == 201, r_create.data
    op_id = r_create.json()["id"]

    r_aprobar = api.post(f"/api/operaciones/{op_id}/aprobar/")
    assert r_aprobar.status_code == 400

    body = r_aprobar.json()
    if "code" in body:
        assert body["code"] == "VALIDATION_ERROR"
        assert "linea_disponible" in body.get("errors", {})
    else:
        assert "linea_disponible" in body
