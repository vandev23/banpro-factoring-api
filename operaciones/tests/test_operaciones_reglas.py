from django.test import TestCase

# Create your tests here.
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from django.utils import timezone

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def _cliente(rut="12.345.678-5", credito="1000000.00", disponible="1000000.00"):
    return Cliente.objects.create(
        rut=rut,
        razon_social="Empresa",
        email="a@a.cl",
        linea_credito=credito,
        linea_disponible=disponible,
        estado=EstadoCliente.ACTIVO,
    )


def _factura(cliente, numero, monto="100000.00", dias_venc=30, estado=EstadoFactura.DISPONIBLE):
    hoy = timezone.localdate()
    return Factura.objects.create(
        cliente=cliente,
        numero_factura=numero,
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=monto,
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=dias_venc),
        estado=estado,
    )


def test_crear_operacion_facturas_de_distinto_cliente_400():
    api = APIClient()
    c1 = _cliente(rut="12.345.678-5", credito="1000000.00", disponible="1000000.00")
    c2 = _cliente(rut="11.111.111-1", credito="1000000.00", disponible="1000000.00")

    f1 = _factura(c1, "F-1")
    f2 = _factura(c2, "F-2")

    resp = api.post("/api/operaciones/", {"cliente": c1.id, "facturas_ids": [f1.id, f2.id]}, format="json")
    assert resp.status_code == 400


def test_crear_operacion_factura_no_disponible_400():
    api = APIClient()
    c1 = _cliente()
    f1 = _factura(c1, "F-1", estado=EstadoFactura.PAGADA)

    resp = api.post("/api/operaciones/", {"cliente": c1.id, "facturas_ids": [f1.id]}, format="json")
    assert resp.status_code == 400


def test_aprobar_operacion_resta_linea_y_cambia_estado_facturas():
    api = APIClient()
    c1 = _cliente(credito="300000.00", disponible="300000.00")
    f1 = _factura(c1, "F-1", monto="100000.00")
    f2 = _factura(c1, "F-2", monto="50000.00")

    r_create = api.post("/api/operaciones/", {"cliente": c1.id, "facturas_ids": [f1.id, f2.id]}, format="json")
    assert r_create.status_code == 201, r_create.data
    op_id = r_create.json()["id"]

    r_aprobar = api.post(f"/api/operaciones/{op_id}/aprobar/")
    assert r_aprobar.status_code == 200, r_aprobar.data

    c1.refresh_from_db()
    assert c1.linea_disponible == Decimal("150000.00")

    f1.refresh_from_db()
    f2.refresh_from_db()
    assert f1.estado == EstadoFactura.CEDIDA
    assert f2.estado == EstadoFactura.CEDIDA
