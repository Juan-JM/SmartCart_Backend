# inventario/views.py
from rest_framework import viewsets, permissions
from .models import Sucursal, Stock
from .serializers import SucursalSerializer, StockSerializer
# Importa permisos necesarios (Reponedor puede gestionar stock?)
from core.permissions import IsAdminOrReadOnly, IsReponedorOrAdmin

class SucursalViewSet(viewsets.ModelViewSet):
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer
    # Cualquiera puede ver, solo Admin puede editar
    permission_classes = [IsAdminOrReadOnly]

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related('producto', 'sucursal').all()
    serializer_class = StockSerializer
    # Solo Reponedores y Admins pueden gestionar el stock
    permission_classes = [IsReponedorOrAdmin]

    # Podrías querer filtrar por sucursal o producto
    # filterset_fields = ['sucursal', 'producto']

    # --- ALERTA DE BAJO STOCK ---
    # Podrías sobreescribir `perform_update` o usar señales (signals)
    # para verificar la cantidad después de una actualización y enviar
    # una notificación si baja de cierto umbral.
    # Esto requiere configurar un sistema de notificaciones (ej. email, push).
