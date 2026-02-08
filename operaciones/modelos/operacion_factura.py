from django.db import models

from facturas.modelos import Factura
from operaciones.modelos.operacion_cesion import OperacionCesion


class OperacionFactura(models.Model):
    operacion = models.ForeignKey(OperacionCesion, on_delete=models.CASCADE)
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["operacion", "factura"], name="uq_operacion_factura")
        ]
