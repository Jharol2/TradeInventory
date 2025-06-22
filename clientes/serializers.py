"""
Serializers para la aplicación de clientes
Convierte los modelos de Django a JSON y viceversa
"""

from rest_framework import serializers
from .models import Cliente, Fiado, DetalleFiado

class ClienteSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Cliente"""
    class Meta:
        model = Cliente
        fields = [
            'id', 'nombre', 'apellido', 'telefono', 'email', 
            'direccion', 'documento', 'activo', 'fecha_registro'
        ]
        read_only_fields = ['id', 'fecha_registro']

class ClienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar clientes"""
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellido', 'telefono', 'email', 'activo']

class ClienteCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear clientes"""
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'email', 'direccion', 'documento']

class DetalleFiadoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo DetalleFiado"""
    class Meta:
        model = DetalleFiado
        fields = [
            'id', 'fiado', 'producto', 'cantidad', 'precio_unitario', 
            'subtotal', 'estado', 'fecha_pago'
        ]
        read_only_fields = ['id', 'subtotal']

class FiadoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Fiado"""
    detalles = DetalleFiadoSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    
    class Meta:
        model = Fiado
        fields = [
            'id', 'cliente', 'cliente_nombre', 'fecha', 'total', 
            'monto_abonado', 'estado', 'detalles'
        ]
        read_only_fields = ['id', 'total'] 