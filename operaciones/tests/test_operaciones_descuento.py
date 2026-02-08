import pytest
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from rest_framework.test import APIClient

from clientes.modelos import Cliente, EstadoCliente
from facturas.modelos import Factura, EstadoFactura

pytestmark = pytest.mark.django_db


def _q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _crear_cliente(linea_disponible="10000000.00"):
    return Cliente.objects.create(
        rut="12.345.678-5",
        razon_social="Empresa Demo",
        email="demo@empresa.cl",
        linea_credito=linea_disponible,
        linea_disponible=linea_disponible,
        estado=EstadoCliente.ACTIVO,
    )


def _crear_factura(cliente, numero, monto, dias_hasta_venc):
    hoy = timezone.localdate()
    return Factura.objects.create(
        cliente=cliente,
        numero_factura=numero,
        rut_deudor="76.543.210-3",
        razon_social_deudor="Deudor",
        monto_total=monto,
        fecha_emision=hoy,
        fecha_vencimiento=hoy + timezone.timedelta(days=dias_hasta_venc),
        estado=EstadoFactura.DISPONIBLE,
    )


def test_descuento_usa_vencimiento_mas_lejano():
    api = APIClient()
    cliente = _crear_cliente()

    # Factura A vence en 10 días, Factura B vence en 40 días => usar 40
    f1 = _crear_factura(cliente, "F-1", Decimal("100000.00"), dias_hasta_venc=10)
    f2 = _crear_factura(cliente, "F-2", Decimal("200000.00"), dias_hasta_venc=40)

    tasa = Decimal("2.00")  # 2%

    resp = api.post(
        "/api/operaciones/",
        {"cliente": cliente.id, "facturas_ids": [f1.id, f2.id], "tasa_descuento": str(tasa)},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    data = resp.json()

    monto_total = Decimal("300000.00")
    dias = Decimal("40")
    esperado_desc = _q2(monto_total * (tasa / Decimal("100")) * (dias / Decimal("360")))
    esperado_desemb = _q2(monto_total - esperado_desc)

    assert Decimal(data["monto_total_facturas"]) == monto_total
    assert Decimal(data["tasa_descuento"]) == tasa
    assert Decimal(data["monto_descuento"]) == esperado_desc
    assert Decimal(data["monto_a_desembolsar"]) == esperado_desemb
