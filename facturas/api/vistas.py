from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from facturas.api.serializadores import SerializadorFactura
from facturas.modelos import Factura
from facturas.selectores import obtener_facturas_filtradas
from facturas.servicios import marcar_pagada, marcar_anulada


class VistaFactura(viewsets.ModelViewSet):
    serializer_class = SerializadorFactura

    def get_queryset(self):
        return obtener_facturas_filtradas(self.request.query_params)

    @action(detail=True, methods=["post"])
    def pagar(self, request, pk=None):
        factura = self.get_object()
        marcar_pagada(factura)
        return Response(self.get_serializer(factura).data)

    @action(detail=True, methods=["post"])
    def anular(self, request, pk=None):
        factura = self.get_object()
        marcar_anulada(factura)
        return Response(self.get_serializer(factura).data)
