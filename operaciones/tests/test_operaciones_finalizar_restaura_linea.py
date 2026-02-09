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


def _factura(cliente, numero, monto, dias=30):
    hoy = timezone.localdate()
    return Factura.objects.create(
        cliente=cliente,
        numero_factura=numero,
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=Decimal(monto),
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=dias),
        estado=EstadoFactura.DISPONIBLE,
    )


def test_finalizar_operacion_restaura_linea_disponible():
    api = APIClient()
    c = _cliente()
    f1 = _factura(c, "F-1", "100000.00")
    f2 = _factura(c, "F-2", "50000.00")

    # crear
    r_create = api.post("/api/operaciones/", {"cliente": c.id, "facturas_ids": [f1.id, f2.id]}, format="json")
    assert r_create.status_code == 201
    op_id = r_create.json()["id"]

    # aprobar => baja línea
    r_aprobar = api.post(f"/api/operaciones/{op_id}/aprobar/")
    assert r_aprobar.status_code == 200

    c.refresh_from_db()
    assert c.linea_disponible == Decimal("150000.00")

    # pagar facturas
    api.post(f"/api/facturas/{f1.id}/pagar/")
    api.post(f"/api/facturas/{f2.id}/pagar/")
    f1.refresh_from_db()
    f2.refresh_from_db()
    assert f1.estado == EstadoFactura.PAGADA
    assert f2.estado == EstadoFactura.PAGADA

    # finalizar => restaura línea
    r_final = api.post(f"/api/operaciones/{op_id}/finalizar/")
    assert r_final.status_code == 200

    c.refresh_from_db()
    assert c.linea_disponible == Decimal("300000.00")
