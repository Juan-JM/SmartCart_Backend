# recomendaciones/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReglaAsociacionViewSet, ConfiguracionRecomendacionViewSet, RecomendacionesAPIView

router = DefaultRouter()
router.register(r'reglas', ReglaAsociacionViewSet, basename='regla-asociacion')
router.register(r'configuracion', ConfiguracionRecomendacionViewSet, basename='configuracion-recomendacion')

urlpatterns = [
    path('', include(router.urls)),
    path('sugerencias/', RecomendacionesAPIView.as_view(), name='sugerencias-productos'),
]