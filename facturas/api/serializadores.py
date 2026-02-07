from decimal import Decimal

from rest_framework import serializers

from core.rut import es_rut_valido, normalizar_rut
from facturas.modelos import Factura, EstadoFactura


class SerializadorFactura(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = [
            "id",
            "cliente",
            "numero_factura",
            "rut_deudor",
            "razon_social_deudor",
            "monto_total",
            "fecha_emision",
            "fecha_vencimiento",
            "estado",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "estado", "creado_en", "actualizado_en"]

    def validate_rut_deudor(self, value: str) -> str:
        if not es_rut_valido(value):
            raise serializers.ValidationError("RUT deudor inválido (formato o dígito verificador).")
        return normalizar_rut(value)

    def validate(self, attrs):
        # Fechas
        fecha_emision = attrs.get("fecha_emision") or (self.instance.fecha_emision if self.instance else None)
        fecha_vencimiento = attrs.get("fecha_vencimiento") or (self.instance.fecha_vencimiento if self.instance else None)

        if fecha_emision and fecha_vencimiento and fecha_vencimiento <= fecha_emision:
            raise serializers.ValidationError(
                {"fecha_vencimiento": "Debe ser posterior a la fecha de emisión."}
            )

        # Monto
        monto = attrs.get("monto_total")
        if monto is not None and monto <= Decimal("0"):
            raise serializers.ValidationError({"monto_total": "Debe ser mayor a 0."})

        # RUT deudor distinto a rut cliente
        cliente = attrs.get("cliente") or (self.instance.cliente if self.instance else None)
        rut_deudor = attrs.get("rut_deudor") or (self.instance.rut_deudor if self.instance else None)

        if cliente and rut_deudor and normalizar_rut(cliente.rut) == normalizar_rut(rut_deudor):
            raise serializers.ValidationError({"rut_deudor": "Debe ser diferente al RUT del cliente."})

        # No permitir crear/editar facturas en estado final a través del CRUD (solo vía acciones)
        if self.instance and self.instance.estado in (EstadoFactura.PAGADA, EstadoFactura.ANULADA):
            raise serializers.ValidationError({"estado": "No se puede modificar una factura pagada o anulada."})

        return attrs
