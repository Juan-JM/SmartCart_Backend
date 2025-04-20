from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from datetime import datetime, timedelta

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    expiration_time = serializers.IntegerField(required=False, default=60)  # Tiempo en minutos
    
    def validate(self, attrs):
        # Elimina expiration_time del diccionario para evitar errores en TokenObtainPairSerializer
        expiration_minutes = attrs.pop('expiration_time', 60)
                  
        # Validación del padre
        data = super().validate(attrs)
        
            # Duración basada en el rol del usuario
        if self.user.is_staff:
            max_expiration = 1440  # 24 horas para personal
        else:
            max_expiration = 120   # 2 horas para clientes normales
    
        if expiration_minutes > max_expiration:
          expiration_minutes = max_expiration

        # Obtener el token creado por el padre
        refresh = self.get_token(self.user)
        
        # Personalizar la expiración del token de acceso
        refresh.access_token.set_exp(
            from_time=datetime.utcnow(),
            lifetime=timedelta(minutes=expiration_minutes)
        )
        
        # Actualizar el token de acceso en la respuesta
        data['access'] = str(refresh.access_token)
        
        # Incluir información del usuario
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['is_staff'] = self.user.is_staff
        data['expiration_minutes'] = expiration_minutes
        
        return data