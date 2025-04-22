# pagos/serializers.py
from rest_framework import serializers
from .models import Pago, EventoStripe

class PagoSerializer(serializers.ModelSerializer):
    nota_venta_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Pago
        fields = (
            'id', 'nota_venta', 'nota_venta_id', 'monto', 
            'stripe_payment_intent_id', 'stripe_payment_method_id',
            'estado', 'fecha_creacion', 'fecha_actualizacion'
        )
        read_only_fields = (
            'id', 'nota_venta', 'estado', 
            'fecha_creacion', 'fecha_actualizacion'
        )

class CrearIntentoPagoSerializer(serializers.Serializer):
    nota_venta_id = serializers.IntegerField(required=True)

class EventoStripeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoStripe
        fields = ('id', 'stripe_id', 'type', 'data', 'procesado', 'fecha_creacion')
        read_only_fields = fields