from decimal import Decimal

def calcular_descuento(monto_total: Decimal, tasa: Decimal, dias_hasta_venc: int) -> tuple[Decimal, Decimal]:
    monto_desc = monto_total * (tasa / Decimal("100")) * (Decimal(dias_hasta_venc) / Decimal("360"))
    monto_desc = monto_desc.quantize(Decimal("0.01"))
    monto_desemb = (monto_total - monto_desc).quantize(Decimal("0.01"))
    return monto_desc, monto_desemb
