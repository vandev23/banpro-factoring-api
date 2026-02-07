import pytest
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente

pytestmark = pytest.mark.django_db


def test_filtro_por_estado():
    Cliente.objects.create(rut="12.345.678-5", razon_social="A", email="a@a.cl", linea_credito="10", linea_disponible="10", estado=EstadoCliente.ACTIVO)
    Cliente.objects.create(rut="11.111.111-1", razon_social="B", email="b@b.cl", linea_credito="10", linea_disponible="10", estado=EstadoCliente.SUSPENDIDO)

    client = APIClient()
    resp = client.get("/api/clientes/?estado=activo")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


def test_filtro_rango_linea_credito():
    Cliente.objects.create(rut="12.345.678-5", razon_social="A", email="a@a.cl", linea_credito="5000", linea_disponible="5000", estado=EstadoCliente.ACTIVO)
    Cliente.objects.create(rut="11.111.111-1", razon_social="B", email="b@b.cl", linea_credito="20000", linea_disponible="20000", estado=EstadoCliente.ACTIVO)

    client = APIClient()
    resp = client.get("/api/clientes/?linea_credito_min=10000")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


def test_filtro_linea_credito_invalido_devuelve_400():
    client = APIClient()
    resp = client.get("/api/clientes/?linea_credito_min=abc")
    assert resp.status_code == 400

    # Si tienes el handler estándar, esto también se puede afirmar:
    body = resp.json()
    assert body.get("code") in (None, "VALIDATION_ERROR")  # tolerante si aún no activas el handler
