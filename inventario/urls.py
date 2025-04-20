# inventario/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SucursalViewSet, StockViewSet

router = DefaultRouter()
router.register(r'sucursales', SucursalViewSet, basename='sucursal') # Pública para lectura
router.register(r'stock', StockViewSet, basename='stock') # Protegida (Reponedor/Admin)

urlpatterns = [
    path('', include(router.urls)),
]