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
        linea_credito="1000000.00",
        linea_disponible="1000000.00",
        estado=EstadoCliente.ACTIVO,
    )


def test_no_permite_crear_operacion_con_factura_vencida():
    api = APIClient()
    c = _cliente()

    hoy = timezone.localdate()
    f_vencida = Factura.objects.create(
        cliente=c,
        numero_factura="F-V",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=Decimal("100000.00"),
        fecha_emision=hoy - timezone.timedelta(days=40),
        fecha_vencimiento=hoy - timezone.timedelta(days=1),  # vencida
        estado=EstadoFactura.DISPONIBLE,
    )

    resp = api.post("/api/operaciones/", {"cliente": c.id, "facturas_ids": [f_vencida.id]}, format="json")
    assert resp.status_code == 400
