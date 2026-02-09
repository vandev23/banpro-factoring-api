import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from decimal import Decimal

from clientes.modelos import Cliente, EstadoCliente

pytestmark = pytest.mark.django_db


def test_no_permite_crear_factura_con_monto_cero():
    api = APIClient()

    cliente = Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa",
        email="a@a.cl",
        linea_credito=Decimal("1000000.00"),
        linea_disponible=Decimal("1000000.00"),
        estado=EstadoCliente.ACTIVO,
    )

    hoy = timezone.localdate()

    resp = api.post(
        "/api/facturas/",
        {
            "cliente": cliente.id,
            "numero_factura": "F-0",
            "rut_deudor": "76.543.210-3",
            "razon_social_deudor": "Deudor",
            "monto_total": "0.00",
            "fecha_emision": str(hoy),
            "fecha_vencimiento": str(hoy + timezone.timedelta(days=30)),
        },
        format="json",
    )

    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "monto_total" in body["errors"]
