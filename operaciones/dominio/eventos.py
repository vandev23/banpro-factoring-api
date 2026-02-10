from core.request_context import request_id_ctx
from operaciones.modelos import OperacionEvento

def registrar_evento(*, operacion, tipo, estado_anterior="", estado_nuevo="", detalle=None):
    payload = dict(detalle or {})
    payload["request_id"] = request_id_ctx.get()
    OperacionEvento.objects.create(
        operacion=operacion,
        tipo=tipo,
        estado_anterior=estado_anterior or "",
        estado_nuevo=estado_nuevo or "",
        detalle=payload,
    )
