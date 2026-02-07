from rest_framework import serializers
from clientes.modelos.cliente import Cliente
from core.rut import normalizar_rut, es_rut_valido


class SerializadorCliente(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id",
            "rut",
            "razon_social",
            "giro",
            "direccion",
            "telefono",
            "email",
            "fecha_registro",
            "linea_credito",
            "linea_disponible",
            "estado",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "fecha_registro", "creado_en", "actualizado_en"]

    def validate_rut(self, value: str) -> str:
        if not es_rut_valido(value):
            raise serializers.ValidationError("RUT inválido (formato o dígito verificador).")
        return normalizar_rut(value)

    def validate(self, attrs):
        # Si no viene linea_disponible al crear, igualarla a linea_credito
        if self.instance is None:
            if attrs.get("linea_credito") is not None and attrs.get("linea_disponible") is None:
                attrs["linea_disponible"] = attrs["linea_credito"]
        return attrs
