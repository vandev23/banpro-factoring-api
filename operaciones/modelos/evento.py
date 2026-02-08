from django.db import models
from django.utils import timezone

from operaciones.modelos.operacion_cesion import OperacionCesion

class TipoEventoOperacion(models.TextChoices):
    CREADA = "creada", "Creada"
    APROBADA = "aprobada", "Aprobada"
    RECHAZADA = "rechazada", "Rechazada"
    DESEMBOLSADA = "desembolsada", "Desembolsada"
    FINALIZADA = "finalizada", "Finalizada"
    ERROR = "error", "Error"


class OperacionEvento(models.Model):
    operacion = models.ForeignKey(OperacionCesion, on_delete=models.CASCADE, related_name="eventos")
    tipo = models.CharField(max_length=20, choices=TipoEventoOperacion.choices)
    fecha = models.DateTimeField(default=timezone.now)

    # “snapshot” útil para auditoría y debugging
    estado_anterior = models.CharField(max_length=20, blank=True, default="")
    estado_nuevo = models.CharField(max_length=20, blank=True, default="")

    detalle = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tipo"]),
            models.Index(fields=["fecha"]),
        ]
