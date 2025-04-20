# ventas/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotaVentaViewSet #, DetalleNotaVentaViewSet

router = DefaultRouter()
router.register(r'notas', NotaVentaViewSet, basename='notaventa')
# Si necesitas el detalle separado:
# router.register(r'detalles', DetalleNotaVentaViewSet, basename='detallenotaventa')

urlpatterns = [
    path('', include(router.urls)),
]