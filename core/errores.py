from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status as http_status


def manejador_excepciones(exc, context):
    resp = exception_handler(exc, context)
    if resp is None:
        # error no manejado por DRF
        return Response(
            {
                "status": "error",
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor",
            },
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalizamos el payload de DRF a nuestro formato
    data = resp.data

    # Si es una validación, normalmente data es dict con fields
    if resp.status_code == 400:
        return Response(
            {
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": "La solicitud contiene datos inválidos",
                "errors": data,
            },
            status=resp.status_code,
        )

    if resp.status_code == 404:
        return Response(
            {
                "status": "error",
                "code": "NOT_FOUND",
                "message": "Recurso no encontrado",
            },
            status=resp.status_code,
        )

    if resp.status_code == 405:
        return Response(
            {
                "status": "error",
                "code": "METHOD_NOT_ALLOWED",
                "message": "Método no permitido",
            },
            status=resp.status_code,
        )

    # fallback genérico
    return Response(
        {
            "status": "error",
            "code": "API_ERROR",
            "message": "Ocurrió un error al procesar la solicitud",
            "details": data,
        },
        status=resp.status_code,
    )
