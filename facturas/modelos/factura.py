from django.db import models
from django.utils import timezone

from clientes.modelos import Cliente
from django.core.validators import MinValueValidator
from decimal import Decimal


class EstadoFactura(models.TextChoices):
    DISPONIBLE = "disponible", "Disponible"
    EN_PROCESO = "en_proceso", "En proceso"
    CEDIDA = "cedida", "Cedida"
    PAGADA = "pagada", "Pagada"
    VENCIDA = "vencida", "Vencida"
    ANULADA = "anulada", "Anulada"


class Factura(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="facturas")

    numero_factura = models.CharField(max_length=50)
    rut_deudor = models.CharField(max_length=12)
    razon_social_deudor = models.CharField(max_length=255)

    monto_total = models.DecimalField(
    max_digits=15,
    decimal_places=2,
    validators=[MinValueValidator(Decimal("0.01"))],)

    fecha_emision = models.DateField()
    fecha_vencimiento = models.DateField()

    estado = models.CharField(
        max_length=20,
        choices=EstadoFactura.choices,
        default=EstadoFactura.DISPONIBLE,
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cliente", "numero_factura"],
                name="uq_factura_cliente_numero",
            )
        ]
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["rut_deudor"]),
            models.Index(fields=["fecha_emision"]),
            models.Index(fields=["fecha_vencimiento"]),
        ]

    def __str__(self) -> str:
        return f"Factura {self.numero_factura} - {self.cliente.rut}"
