# pagos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PagoViewSet, 
    CrearIntentoPagoAPIView, 
    ConfirmarPagoAPIView,
    stripe_webhook
)

router = DefaultRouter()
router.register(r'pagos', PagoViewSet, basename='pago')

urlpatterns = [
    path('', include(router.urls)),
    path('crear-intento/', CrearIntentoPagoAPIView.as_view(), name='crear-intento'),
    path('confirmar-pago/', ConfirmarPagoAPIView.as_view(), name='confirmar-pago'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]