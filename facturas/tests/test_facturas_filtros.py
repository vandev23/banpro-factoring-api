import pytest
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def _cliente(rut: str, email: str):
    return Cliente.objects.create(
        rut=rut,
        razon_social=f"Empresa {rut}",
        email=email,
        linea_credito="10000000.00",
        linea_disponible="10000000.00",
        estado=EstadoCliente.ACTIVO,
    )


def test_filtro_por_cliente_id_y_estado():
    client = APIClient()

    c1 = _cliente("12.345.678-5", "a@a.cl")
    c2 = _cliente("11.111.111-1", "b@b.cl")

    Factura.objects.create(
        cliente=c1,
        numero_factura="F-1",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total="1000.00",
        fecha_emision="2026-02-01",
        fecha_vencimiento="2026-03-01",
        estado=EstadoFactura.DISPONIBLE,
    )
    Factura.objects.create(
        cliente=c2,
        numero_factura="F-2",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total="1000.00",
        fecha_emision="2026-02-01",
        fecha_vencimiento="2026-03-01",
        estado=EstadoFactura.PAGADA,
    )

    resp = client.get(f"/api/facturas/?cliente_id={c1.id}&estado=disponible")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


def test_filtro_por_rut_deudor():
    client = APIClient()
    c1 = _cliente("12.345.678-5", "a@a.cl")

    Factura.objects.create(
        cliente=c1,
        numero_factura="F-10",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total="1000.00",
        fecha_emision="2026-02-01",
        fecha_vencimiento="2026-03-01",
        estado=EstadoFactura.DISPONIBLE,
    )

    resp = client.get("/api/facturas/?rut_deudor=76.543.210-3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


def test_filtro_por_rango_fechas_emision():
    client = APIClient()
    c1 = _cliente("12.345.678-5", "a@a.cl")

    Factura.objects.create(
        cliente=c1,
        numero_factura="F-20",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total="1000.00",
        fecha_emision="2026-01-01",
        fecha_vencimiento="2026-02-01",
        estado=EstadoFactura.DISPONIBLE,
    )
    Factura.objects.create(
        cliente=c1,
        numero_factura="F-21",
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total="1000.00",
        fecha_emision="2026-02-15",
        fecha_vencimiento="2026-03-15",
        estado=EstadoFactura.DISPONIBLE,
    )

    resp = client.get("/api/facturas/?fecha_desde=2026-02-01&fecha_hasta=2026-02-28")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


def test_filtro_fecha_invalida_devuelve_400_con_wrapper_si_existe():
    client = APIClient()
    resp = client.get("/api/facturas/?fecha_desde=01-02-2026")
    assert resp.status_code == 400
    body = resp.json()

    # Si el wrapper está activo
    if "code" in body:
        assert body["code"] == "VALIDATION_ERROR"
        assert "fecha_desde" in body.get("errors", {})
    else:
        # Respuesta DRF clásica
        assert "fecha_desde" in body
