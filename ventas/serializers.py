"""
Serializers para la aplicación de ventas
Convierte los modelos de Django a JSON y viceversa
"""

from rest_framework import serializers
from .models import Venta, DetalleVenta
from productos.models import Producto
from clientes.models import Cliente

class ProductoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para productos en ventas"""
    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio']

class ClienteSerializer(serializers.ModelSerializer):
    """Serializer simplificado para clientes en ventas"""
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellido']

class DetalleVentaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo DetalleVenta"""
    producto = ProductoSerializer(read_only=True)
    producto_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DetalleVenta
        fields = [
            'id', 'venta', 'producto', 'producto_id', 'cantidad', 
            'precio_unitario', 'subtotal'
        ]
        read_only_fields = ['id', 'precio_unitario', 'subtotal']

class VentaSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Venta"""
    detalles = DetalleVentaSerializer(many=True, read_only=True)
    cliente = ClienteSerializer(read_only=True)
    cliente_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Venta
        fields = [
            'id', 'cliente', 'cliente_id', 'fecha', 'total', 
            'es_fiado', 'monto_abonado', 'estado', 'detalles'
        ]
        read_only_fields = ['id', 'fecha', 'total']

class VentaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar ventas"""
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    
    class Meta:
        model = Venta
        fields = [
            'id', 'cliente_nombre', 'fecha', 'total', 
            'es_fiado', 'monto_abonado', 'estado'
        ]

class VentaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear ventas"""
    detalles = DetalleVentaSerializer(many=True)
    
    class Meta:
        model = Venta
        fields = ['cliente_id', 'es_fiado', 'detalles']
    
    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        venta = Venta.objects.create(**validated_data)
        
        total_venta = 0
        for detalle_data in detalles_data:
            producto = Producto.objects.get(id=detalle_data['producto_id'])
            cantidad = detalle_data['cantidad']
            precio = producto.precio
            subtotal = precio * cantidad
            
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=subtotal
            )
            
            # Actualizar stock
            producto.stock_actual -= cantidad
            producto.save()
            
            total_venta += subtotal
        
        venta.total = total_venta
        venta.save()
        
        return venta 