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
        linea_credito="200000.00",
        linea_disponible="200000.00",
        estado=EstadoCliente.ACTIVO,
    )


def _factura(cliente, numero):
    hoy = timezone.localdate()
    return Factura.objects.create(
        cliente=cliente,
        numero_factura=numero,
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=Decimal("100000.00"),
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=30),
        estado=EstadoFactura.DISPONIBLE,
    )


def test_rechazar_sin_motivo_da_400():
    api = APIClient()
    c = _cliente()
    f1 = _factura(c, "F-1")

    r_create = api.post("/api/operaciones/", {"cliente": c.id, "facturas_ids": [f1.id]}, format="json")
    op_id = r_create.json()["id"]

    r_rech = api.post(f"/api/operaciones/{op_id}/rechazar/", {"motivo_rechazo": ""}, format="json")
    assert r_rech.status_code == 400


def test_rechazar_no_modifica_linea_ni_estado_factura():
    api = APIClient()
    c = _cliente()
    f1 = _factura(c, "F-1")

    r_create = api.post("/api/operaciones/", {"cliente": c.id, "facturas_ids": [f1.id]}, format="json")
    op_id = r_create.json()["id"]

    r_rech = api.post(f"/api/operaciones/{op_id}/rechazar/", {"motivo_rechazo": "Riesgo alto"}, format="json")
    assert r_rech.status_code == 200

    c.refresh_from_db()
    f1.refresh_from_db()
    assert c.linea_disponible == Decimal("200000.00")
    assert f1.estado == EstadoFactura.DISPONIBLE
