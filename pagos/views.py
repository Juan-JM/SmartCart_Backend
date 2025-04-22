# pagos/views.py
import stripe
import json
from decimal import Decimal

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Pago, EventoStripe
from .serializers import PagoSerializer, CrearIntentoPagoSerializer, EventoStripeSerializer
from ventas.models import NotaVenta
from core.permissions import IsVendedorOrAdmin, IsCliente

# Configuración de Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

class PagoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar los pagos."""
    serializer_class = PagoSerializer
    
    def get_queryset(self):
        """Filtrar pagos: Admins/Vendedores ven todos, Clientes solo los suyos."""
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Vendedor').exists():
            return Pago.objects.select_related('nota_venta').all()
        elif hasattr(user, 'cliente_profile'):
            return Pago.objects.filter(
                nota_venta__cliente=user.cliente_profile
            ).select_related('nota_venta')
        return Pago.objects.none()
    
    def get_permissions(self):
        """Define permisos por acción."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class CrearIntentoPagoAPIView(APIView):
    """Vista para crear un intento de pago (Payment Intent) en Stripe."""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = CrearIntentoPagoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        nota_venta_id = serializer.validated_data['nota_venta_id']
        
        try:
            # Obtener la nota de venta
            nota_venta = NotaVenta.objects.get(id=nota_venta_id)
            
            # Simplificamos la lógica de permisos:
            user = request.user
            
            # Caso 1: Si el usuario es staff o vendedor, permitir acceso
            is_staff_or_vendedor = user.is_staff or user.groups.filter(name='Vendedor').exists()
            
            # Caso 2: Si la nota no tiene cliente, cualquier usuario autenticado puede pagarla
            is_anonymous_purchase = nota_venta.cliente is None
            
            # Caso 3: Si la nota tiene cliente, el usuario debe ser ese cliente
            is_owner = False
            if nota_venta.cliente and hasattr(user, 'cliente_profile'):
                is_owner = nota_venta.cliente.id == user.cliente_profile.id
            
            # Si no cumple ninguna condición, denegar acceso
            if not (is_staff_or_vendedor or is_anonymous_purchase or is_owner):
                return Response(
                    {"detail": "No tienes permiso para pagar esta nota de venta."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verificar si ya existe un pago para esta nota de venta
            pago_existente = Pago.objects.filter(nota_venta=nota_venta).first()
            if pago_existente:
                # Si existe y está en estado pendiente, devolver el intento existente
                if pago_existente.estado == 'pendiente' and pago_existente.stripe_payment_intent_id:
                    payment_intent = stripe.PaymentIntent.retrieve(
                        pago_existente.stripe_payment_intent_id
                    )
                    if payment_intent.status != 'succeeded':
                        return Response({
                            'clientSecret': payment_intent.client_secret,
                            'payment_intent_id': payment_intent.id,
                            'amount': float(pago_existente.monto)
                        })
                
                # Si existe y no es pendiente o no tiene ID, informar que ya se procesó
                return Response(
                    {"detail": f"Esta nota de venta ya tiene un pago en estado {pago_existente.estado}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convertir monto a centavos para Stripe (Stripe usa la moneda menor)
            amount_in_cents = int(nota_venta.monto_total * 100)
            
            # Crear el PaymentIntent en Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_in_cents,
                currency='usd',  # Cambiar según tu moneda
                metadata={
                    'nota_venta_id': nota_venta.id,
                    'cliente_id': nota_venta.cliente.id if nota_venta.cliente else None,
                },
            )
            
            # Crear registro de pago en nuestro sistema
            pago = Pago.objects.create(
                nota_venta=nota_venta,
                monto=nota_venta.monto_total,
                stripe_payment_intent_id=payment_intent.id,
                estado='pendiente'
            )
            
            # Devolver el client_secret para que el frontend pueda completar el pago
            return Response({
                'clientSecret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': float(nota_venta.monto_total)
            })
            
        except NotaVenta.DoesNotExist:
            return Response(
                {"detail": "La nota de venta no existe."},
                status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            # Registrar el error y devolver respuesta adecuada
            print(f"Error Stripe: {str(e)}")
            return Response(
                {"detail": f"Error al procesar el pago: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Registrar el error genérico
            print(f"Error inesperado: {str(e)}")
            return Response(
                {"detail": "Error inesperado al procesar la solicitud."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConfirmarPagoAPIView(APIView):
    """Vista para confirmar que un pago ha sido completado."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        payment_intent_id = request.data.get('payment_intent_id')
        
        if not payment_intent_id:
            return Response(
                {"detail": "ID de PaymentIntent no proporcionado."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verificar el estado del pago en Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Actualizar el estado en nuestro sistema
            pago = Pago.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
            
            if not pago:
                return Response(
                    {"detail": "Pago no encontrado en nuestro sistema."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verificación de permisos simplificada, similar a CrearIntentoPagoAPIView
            user = request.user
            
            # Caso 1: Si el usuario es staff o vendedor, permitir acceso
            is_staff_or_vendedor = user.is_staff or user.groups.filter(name='Vendedor').exists()
            
            # Caso 2: Si la nota no tiene cliente, cualquier usuario autenticado puede confirmar
            is_anonymous_purchase = pago.nota_venta.cliente is None
            
            # Caso 3: Si la nota tiene cliente, el usuario debe ser ese cliente
            is_owner = False
            if pago.nota_venta.cliente and hasattr(user, 'cliente_profile'):
                is_owner = pago.nota_venta.cliente.id == user.cliente_profile.id
            
            # Si no cumple ninguna condición, denegar acceso
            if not (is_staff_or_vendedor or is_anonymous_purchase or is_owner):
                return Response(
                    {"detail": "No tienes permiso para confirmar este pago."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Actualizar estado según la respuesta de Stripe
            if payment_intent.status == 'succeeded':
                pago.estado = 'completado'
                pago.stripe_payment_method_id = payment_intent.payment_method
                pago.save()
                
                # Actualizar el estado de la nota de venta
                nota_venta = pago.nota_venta
                nota_venta.estado = 'pagada'
                nota_venta.save()
                
                return Response({
                    "estado": "completado",
                    "mensaje": "Pago procesado correctamente"
                })
            else:
                pago.estado = 'pendiente' if payment_intent.status in ['processing', 'requires_confirmation'] else 'fallido'
                pago.save()
                
                return Response({
                    "estado": pago.estado,
                    "mensaje": f"Estado del pago: {payment_intent.status}"
                })
                
        except stripe.error.StripeError as e:
            return Response(
                {"detail": f"Error al verificar el pago: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Error inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            


@csrf_exempt
def stripe_webhook(request):
    """
    Vista para recibir y procesar webhooks de Stripe.
    Esta vista no requiere autenticación ya que Stripe la llamará directamente.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        # Verificar la firma del webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        
        # Guardar el evento en la base de datos
        EventoStripe.objects.create(
            stripe_id=event['id'],
            type=event['type'],
            data=event
        )
        
        # Procesar eventos específicos
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            _handle_payment_succeeded(payment_intent)
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            _handle_payment_failed(payment_intent)
        
        return HttpResponse(status=200)
    
    except ValueError as e:
        # Payload inválido
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Firma inválida
        return HttpResponse(status=400)
    except Exception as e:
        print(f"Error en webhook: {str(e)}")
        return HttpResponse(status=500)


def _handle_payment_succeeded(payment_intent):
    """Maneja el evento de pago exitoso."""
    payment_intent_id = payment_intent['id']
    
    try:
        with transaction.atomic():
            # Actualizar estado del pago
            pago = Pago.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
            if pago:
                pago.estado = 'completado'
                pago.stripe_payment_method_id = payment_intent.get('payment_method')
                pago.save()
                
                # Actualizar estado de la nota de venta
                nota_venta = pago.nota_venta
                nota_venta.estado = 'pagada'
                nota_venta.save()
                
                # Aquí puedes realizar acciones adicionales como:
                # - Enviar confirmación por email
                # - Actualizar inventario
                # - Actualizar puntos de cliente
    except Exception as e:
        print(f"Error al procesar pago exitoso: {str(e)}")

def _handle_payment_failed(payment_intent):
    """Maneja el evento de pago fallido."""
    payment_intent_id = payment_intent['id']
    
    try:
        with transaction.atomic():
            # Actualizar estado del pago
            pago = Pago.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
            if pago:
                pago.estado = 'fallido'
                pago.save()
                
                # Puedes decidir si actualizar el estado de la nota de venta
                # o mantenerla como 'pendiente' para permitir reintentos
    except Exception as e:
        print(f"Error al procesar pago fallido: {str(e)}")