from rest_framework.routers import DefaultRouter
from clientes.api.vistas import VistaCliente

router = DefaultRouter()
router.register(r"clientes", VistaCliente, basename="clientes")

urlpatterns = router.urls
