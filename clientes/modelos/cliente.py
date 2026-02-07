from django.db import models
from django.utils import timezone


class EstadoCliente(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    ACTIVO = "activo", "Activo"
    SUSPENDIDO = "suspendido", "Suspendido"
    BLOQUEADO = "bloqueado", "Bloqueado"


class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    razon_social = models.CharField(max_length=255)
    giro = models.CharField(max_length=255, blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    telefono = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField()

    fecha_registro = models.DateTimeField(default=timezone.now)

    linea_credito = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    linea_disponible = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    estado = models.CharField(
        max_length=20,
        choices=EstadoCliente.choices,
        default=EstadoCliente.PENDIENTE,
    )

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["linea_credito"]),
        ]

    def __str__(self) -> str:
        return f"{self.razon_social} ({self.rut})"
