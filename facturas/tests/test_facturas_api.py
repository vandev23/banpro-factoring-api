import pytest
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def _crear_cliente():
    return Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa Demo SpA",
        email="demo@empresa.cl",
        linea_credito="10000000.00",
        linea_disponible="10000000.00",
        estado=EstadoCliente.ACTIVO,
    )


def test_crear_factura_ok_normaliza_rut_deudor():
    client = APIClient()
    cliente = _crear_cliente()

    payload = {
        "cliente": cliente.id,
        "numero_factura": "F-1001",
        "rut_deudor": "76543210-3",  # sin puntos
        "razon_social_deudor": "Deudor Uno SpA",
        "monto_total": "1500000.00",
        "fecha_emision": "2026-02-01",
        "fecha_vencimiento": "2026-03-01",
    }

    resp = client.post("/api/facturas/", payload, format="json")
    assert resp.status_code == 201, resp.data

    data = resp.json()
    assert data["cliente"] == cliente.id
    assert data["numero_factura"] == "F-1001"
    assert data["rut_deudor"] == "76.543.210-3"  # normalizado
    assert data["estado"] == EstadoFactura.DISPONIBLE


def test_no_permite_fecha_vencimiento_menor_o_igual_a_emision():
    client = APIClient()
    cliente = _crear_cliente()

    payload = {
        "cliente": cliente.id,
        "numero_factura": "F-1002",
        "rut_deudor": "76.543.210-3",
        "razon_social_deudor": "Deudor Dos SpA",
        "monto_total": "1000.00",
        "fecha_emision": "2026-03-01",
        "fecha_vencimiento": "2026-03-01",  # igual
    }

    resp = client.post("/api/facturas/", payload, format="json")
    assert resp.status_code == 400
    body = resp.json()
    # si tienes wrapper global:
    if "code" in body:
        assert body["code"] == "VALIDATION_ERROR"
        assert "fecha_vencimiento" in body.get("errors", {})
    else:
        assert "fecha_vencimiento" in body


def test_no_permite_rut_deudor_igual_al_cliente():
    client = APIClient()
    cliente = _crear_cliente()

    payload = {
        "cliente": cliente.id,
        "numero_factura": "F-1003",
        "rut_deudor": "12.345.678-5",  # igual al cliente
        "razon_social_deudor": "Deudor",
        "monto_total": "1000.00",
        "fecha_emision": "2026-02-01",
        "fecha_vencimiento": "2026-03-01",
    }

    resp = client.post("/api/facturas/", payload, format="json")
    assert resp.status_code == 400
    body = resp.json()
    if "code" in body:
        assert body["code"] == "VALIDATION_ERROR"
        assert "rut_deudor" in body.get("errors", {})
    else:
        assert "rut_deudor" in body


def test_no_permite_monto_cero_o_negativo():
    client = APIClient()
    cliente = _crear_cliente()

    payload = {
        "cliente": cliente.id,
        "numero_factura": "F-1004",
        "rut_deudor": "76.543.210-3",
        "razon_social_deudor": "Deudor",
        "monto_total": "0.00",
        "fecha_emision": "2026-02-01",
        "fecha_vencimiento": "2026-03-01",
    }

    resp = client.post("/api/facturas/", payload, format="json")
    assert resp.status_code == 400


def test_numero_factura_unico_por_cliente():
    client = APIClient()
    cliente = _crear_cliente()

    payload = {
        "cliente": cliente.id,
        "numero_factura": "F-2000",
        "rut_deudor": "76.543.210-3",
        "razon_social_deudor": "Deudor",
        "monto_total": "1000.00",
        "fecha_emision": "2026-02-01",
        "fecha_vencimiento": "2026-03-01",
    }

    r1 = client.post("/api/facturas/", payload, format="json")
    assert r1.status_code == 201, r1.data

    r2 = client.post("/api/facturas/", payload, format="json")
    assert r2.status_code == 400


def test_acciones_pagar_y_anular_cambian_estado():
    client = APIClient()
    cliente = _crear_cliente()

    factura = Factura.objects.create(
        cliente=cliente,
        numero_factura="F-3000",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total="5000.00",
        fecha_emision="2026-02-01",
        fecha_vencimiento="2026-03-01",
        estado=EstadoFactura.DISPONIBLE,
    )

    r_pagar = client.post(f"/api/facturas/{factura.id}/pagar/")
    assert r_pagar.status_code == 200, r_pagar.data
    factura.refresh_from_db()
    assert factura.estado == EstadoFactura.PAGADA

    r_anular = client.post(f"/api/facturas/{factura.id}/anular/")
    assert r_anular.status_code == 200, r_anular.data
    factura.refresh_from_db()
    assert factura.estado == EstadoFactura.ANULADA
