from decimal import Decimal, InvalidOperation

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from clientes.modelos import Cliente
from clientes.api.serializadores import SerializadorCliente
from clientes.servicios import activar_cliente, suspender_cliente


class VistaCliente(viewsets.ModelViewSet):
    serializer_class = SerializadorCliente

    def _parse_decimal_param(self, name: str, value: str) -> Decimal:
        try:
            dec = Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValidationError({name: f"Valor inválido para {name}: '{value}' (debe ser numérico)."})
        if dec < 0:
            raise ValidationError({name: f"{name} no puede ser negativo."})
        return dec

    def get_queryset(self):
        qs = Cliente.objects.all().order_by("-creado_en")
        params = self.request.query_params

        # 1) estado
        estado = params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)

        # 2) rangos línea de crédito
        linea_min = params.get("linea_credito_min")
        if linea_min is not None and linea_min != "":
            dec_min = self._parse_decimal_param("linea_credito_min", linea_min)
            qs = qs.filter(linea_credito__gte=dec_min)

        linea_max = params.get("linea_credito_max")
        if linea_max is not None and linea_max != "":
            dec_max = self._parse_decimal_param("linea_credito_max", linea_max)
            qs = qs.filter(linea_credito__lte=dec_max)

        if linea_min and linea_max:
            # Validación lógica: min <= max
            if dec_min > dec_max:
                raise ValidationError({"linea_credito": "linea_credito_min no puede ser mayor que linea_credito_max."})

        # 3) búsqueda opcional (rut o razón social)
        q = params.get("q")
        if q:
            qs = qs.filter(razon_social__icontains=q) | qs.filter(rut__icontains=q)

        return qs

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        cliente = self.get_object()
        activar_cliente(cliente)
        return Response(self.get_serializer(cliente).data)

    @action(detail=True, methods=["post"])
    def suspender(self, request, pk=None):
        cliente = self.get_object()
        suspender_cliente(cliente)
        return Response(self.get_serializer(cliente).data)

    @action(detail=True, methods=["get"], url_path="linea-disponible")
    def linea_disponible(self, request, pk=None):
        cliente = self.get_object()
        return Response(
            {
                "cliente_id": cliente.id,
                "linea_credito": str(cliente.linea_credito),
                "linea_disponible": str(cliente.linea_disponible),
            }
        )
