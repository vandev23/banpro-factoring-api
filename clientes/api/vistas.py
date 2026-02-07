from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from clientes.api.serializadores import SerializadorCliente
from clientes.selectores import obtener_clientes_filtrados
from clientes.servicios import activar_cliente, suspender_cliente


class VistaCliente(viewsets.ModelViewSet):
    serializer_class = SerializadorCliente

    def get_queryset(self):
        return obtener_clientes_filtrados(self.request.query_params)

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
