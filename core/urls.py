# core/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView, 
)
#imagen
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('',admin.site.urls,name='index'),
    path('admin/', admin.site.urls),
    path('api/', include('authentication.urls')),
    # Endpoints de Autenticación JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # POST para obtener tokens (login)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),  

    path('api/usuarios/', include('usuarios.urls')),
    path('api/productos/', include('productos.urls')),
    path('api/inventario/', include('inventario.urls')),
    path('api/ventas/', include('ventas.urls')),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  

