import uuid
from core.request_context import request_id_ctx

class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        request.request_id = request_id
        request_id_ctx.set(request_id)

        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
