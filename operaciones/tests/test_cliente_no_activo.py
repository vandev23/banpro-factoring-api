import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def test_no_se_puede_crear_operacion_si_cliente_no_activo():
    api = APIClient()

    cliente = Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa",
        email="a@a.cl",
        linea_credito=Decimal("1000000.00"),
        linea_disponible=Decimal("1000000.00"),
        estado=EstadoCliente.SUSPENDIDO,  # <-- no activo
    )

    hoy = timezone.localdate()
    factura = Factura.objects.create(
        cliente=cliente,
        numero_factura="F-1",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=Decimal("100000.00"),
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=30),
        estado=EstadoFactura.DISPONIBLE,
    )

    resp = api.post(
        "/api/operaciones/",
        {"cliente": cliente.id, "facturas_ids": [factura.id]},
        format="json",
    )

    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "cliente" in body["errors"]
