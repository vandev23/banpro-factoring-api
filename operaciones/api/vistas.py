from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from operaciones.api.serializadores import SerializadorOperacion, SerializadorRechazo
from operaciones.modelos import OperacionCesion
from operaciones.selectores import obtener_operaciones_filtradas
from operaciones.servicios import (
    crear_operacion,
    aprobar_operacion,
    rechazar_operacion,
    registrar_desembolso,
    finalizar_operacion_si_pagada,
)
from operaciones.modelos import OperacionEvento


class VistaOperacion(viewsets.ModelViewSet):
    serializer_class = SerializadorOperacion

    def get_queryset(self):
        return obtener_operaciones_filtradas(self.request.query_params)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        operacion = crear_operacion(
            cliente_id=serializer.validated_data["cliente"].id,
            facturas_ids=serializer.validated_data["facturas_ids"],
            tasa_descuento=serializer.validated_data.get("tasa_descuento"),
        )
        return Response(self.get_serializer(operacion).data, status=201)

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        operacion = aprobar_operacion(int(pk))
        return Response(self.get_serializer(operacion).data)

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        s = SerializadorRechazo(data=request.data)
        s.is_valid(raise_exception=True)

        operacion = rechazar_operacion(int(pk), s.validated_data["motivo_rechazo"])
        return Response(self.get_serializer(operacion).data)

    @action(detail=True, methods=["post"], url_path="desembolsar")
    def desembolsar(self, request, pk=None):
        operacion = registrar_desembolso(int(pk))
        return Response(self.get_serializer(operacion).data)

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        operacion = finalizar_operacion_si_pagada(int(pk))
        return Response(self.get_serializer(operacion).data)
    
    @action(detail=True, methods=["get"], url_path="eventos")
    def eventos(self, request, pk=None):
        eventos = OperacionEvento.objects.filter(operacion_id=pk).order_by("fecha")
        data = [
            {
                "id": e.id,
                "tipo": e.tipo,
                "fecha": e.fecha.isoformat(),
                "estado_anterior": e.estado_anterior,
                "estado_nuevo": e.estado_nuevo,
                "detalle": e.detalle,
            }
            for e in eventos
        ]
        return Response({"operacion_id": int(pk), "eventos": data})

