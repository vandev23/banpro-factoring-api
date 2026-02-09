import pytest
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def test_usa_tasa_por_defecto_desde_settings(settings):

    api = APIClient()

    cliente = Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa",
        email="test@test.cl",
        linea_credito="1000000.00",
        linea_disponible="1000000.00",
        estado=EstadoCliente.ACTIVO,
    )

    hoy = timezone.localdate()
    factura = Factura.objects.create(
        cliente=cliente,
        numero_factura="F-100",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total="100000.00",
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=30),
        estado=EstadoFactura.DISPONIBLE,
    )

    resp = api.post(
        "/api/operaciones/",
        {"cliente": cliente.id, "facturas_ids": [factura.id]},
        format="json",
    )

    assert resp.status_code == 201
    assert Decimal(resp.json()["tasa_descuento"]) == Decimal(settings.DEFAULT_TASA_DESCUENTO)
