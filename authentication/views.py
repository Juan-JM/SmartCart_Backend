from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Llamada al método post del padre
        response = super().post(request, *args, **kwargs)
        
        # Si hay un error, simplemente devuelve la respuesta original
        if response.status_code != status.HTTP_200_OK:
            return response
            
        return response

# También podemos extender TokenRefreshView si necesitamos personalizar la renovación
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Aquí puedes agregar lógica adicional si es necesario
        return response