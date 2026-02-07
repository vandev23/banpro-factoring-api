from rest_framework.routers import DefaultRouter
from facturas.api.vistas import VistaFactura

router = DefaultRouter()
router.register(r"facturas", VistaFactura, basename="facturas")

urlpatterns = router.urls
