from django.db import models
from django.utils import timezone

from clientes.modelos import Cliente
from facturas.modelos import Factura


class EstadoOperacion(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    APROBADA = "aprobada", "Aprobada"
    RECHAZADA = "rechazada", "Rechazada"
    DESEMBOLSADA = "desembolsada", "Desembolsada"
    FINALIZADA = "finalizada", "Finalizada"


class OperacionCesion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="operaciones")

    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_desembolso = models.DateTimeField(null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)

    monto_total_facturas = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tasa_descuento = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)  # %
    monto_descuento = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    monto_a_desembolsar = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    motivo_rechazo = models.TextField(blank=True, default="")

    estado = models.CharField(
        max_length=20,
        choices=EstadoOperacion.choices,
        default=EstadoOperacion.PENDIENTE,
    )

    facturas = models.ManyToManyField(Factura, through="OperacionFactura", related_name="operaciones")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["fecha_solicitud"]),
        ]

    def __str__(self) -> str:
        return f"Operación {self.id} - {self.cliente.rut} - {self.estado}"
