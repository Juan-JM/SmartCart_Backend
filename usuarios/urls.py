# usuarios/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegistrationAPIView, UserViewSet, ClienteViewSet, PersonalViewSet,
    UserProfileAPIView, ChangePasswordAPIView,GroupViewSet, PermissionViewSet # Nombres de vista confirmados
)
# from .views import (
#     RegistrationAPIView, UserViewSet, ClienteViewSet, PersonalViewSet,
#     UserProfileAPIView, ChangePasswordAPIView
# )

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'personal', PersonalViewSet, basename='personal')
router.register(r'grupos', GroupViewSet, basename='group')    # Añadir esta línea
router.register(r'permisos', PermissionViewSet, basename='permission')    # Añadir esta línea

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change-password'),
]
