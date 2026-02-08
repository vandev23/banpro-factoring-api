from rest_framework import serializers

from operaciones.modelos import OperacionCesion, EstadoOperacion


class SerializadorOperacion(serializers.ModelSerializer):
    facturas_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=False,
    )

    class Meta:
        model = OperacionCesion
        fields = [
            "id",
            "cliente",
            "fecha_solicitud",
            "fecha_aprobacion",
            "fecha_desembolso",
            "fecha_finalizacion",
            "monto_total_facturas",
            "tasa_descuento",
            "monto_descuento",
            "monto_a_desembolsar",
            "estado",
            "motivo_rechazo",
            "facturas_ids",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id",
            "fecha_solicitud",
            "fecha_aprobacion",
            "fecha_desembolso",
            "fecha_finalizacion",
            "monto_total_facturas",
            "monto_descuento",
            "monto_a_desembolsar",
            "estado",
            "motivo_rechazo",
            "creado_en",
            "actualizado_en",
        ]


class SerializadorRechazo(serializers.Serializer):
    motivo_rechazo = serializers.CharField(min_length=3)
