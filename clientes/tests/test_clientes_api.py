import pytest
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente


pytestmark = pytest.mark.django_db


def test_crear_cliente_normaliza_rut_y_setea_linea_disponible():
    client = APIClient()

    payload = {
        "rut": "12345678-5",  # sin puntos
        "razon_social": "Empresa Demo SpA",
        "giro": "Servicios",
        "direccion": "Santiago",
        "telefono": "+56 9 1111 1111",
        "email": "demo@empresa.cl",
        "linea_credito": "10000000.00",
        # no enviamos linea_disponible a propósito
    }

    resp = client.post("/api/clientes/", payload, format="json")
    assert resp.status_code == 201, resp.data

    data = resp.json()
    assert data["rut"] == "12.345.678-5"
    assert data["linea_credito"] == "10000000.00"
    assert data["linea_disponible"] == "10000000.00"


def test_crear_cliente_rut_invalido_retorna_400():
    client = APIClient()

    payload = {
        "rut": "12.345.678-0",  # DV incorrecto
        "razon_social": "Empresa X",
        "email": "x@x.cl",
        "linea_credito": "1.00",
    }

    resp = client.post("/api/clientes/", payload, format="json")
    assert resp.status_code == 400


def test_rut_unico_no_permite_duplicados():
    client = APIClient()

    payload = {
        "rut": "12.345.678-5",
        "razon_social": "Empresa 1",
        "email": "a@a.cl",
        "linea_credito": "100.00",
    }

    r1 = client.post("/api/clientes/", payload, format="json")
    assert r1.status_code == 201, r1.data

    payload2 = {
        "rut": "12.345.678-5",
        "razon_social": "Empresa 2",
        "email": "b@b.cl",
        "linea_credito": "200.00",
    }
    r2 = client.post("/api/clientes/", payload2, format="json")
    assert r2.status_code == 400


def test_acciones_activar_y_suspender_cambian_estado():
    client = APIClient()

    cliente = Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa Demo",
        email="demo@demo.cl",
        linea_credito="1000.00",
        linea_disponible="1000.00",
        estado=EstadoCliente.PENDIENTE,
    )

    r_activar = client.post(f"/api/clientes/{cliente.id}/activar/")
    assert r_activar.status_code == 200
    cliente.refresh_from_db()
    assert cliente.estado == EstadoCliente.ACTIVO

    r_suspender = client.post(f"/api/clientes/{cliente.id}/suspender/")
    assert r_suspender.status_code == 200
    cliente.refresh_from_db()
    assert cliente.estado == EstadoCliente.SUSPENDIDO


def test_endpoint_linea_disponible():
    client = APIClient()

    cliente = Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa Demo",
        email="demo@demo.cl",
        linea_credito="5000.00",
        linea_disponible="3000.00",
        estado=EstadoCliente.ACTIVO,
    )

    resp = client.get(f"/api/clientes/{cliente.id}/linea-disponible/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["linea_credito"] == "5000.00"
    assert data["linea_disponible"] == "3000.00"
