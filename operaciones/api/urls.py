from rest_framework.routers import DefaultRouter
from operaciones.api.vistas import VistaOperacion

router = DefaultRouter()
router.register(r"operaciones", VistaOperacion, basename="operaciones")

urlpatterns = router.urls
