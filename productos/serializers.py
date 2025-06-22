"""
Serializers para la aplicación de productos
Convierte los modelos de Django a JSON y viceversa
"""

from rest_framework import serializers
from .models import Producto
from categorias.models import Categoria
from proveedores.models import Proveedor

class CategoriaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Categoria"""
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'activo']

class ProveedorSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Proveedor"""
    class Meta:
        model = Proveedor
        fields = ['id', 'nombre', 'telefono', 'email', 'direccion', 'activo']

class ProductoSerializer(serializers.ModelSerializer):
    """Serializer completo para el modelo Producto"""
    categoria = CategoriaSerializer(read_only=True)
    proveedor = ProveedorSerializer(read_only=True)
    categoria_id = serializers.IntegerField(write_only=True, required=False)
    proveedor_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio', 'stock_actual', 
            'stock_minimo', 'categoria', 'proveedor', 'imagen', 
            'activo', 'fecha_creacion', 'categoria_id', 'proveedor_id'
        ]
        read_only_fields = ['id', 'fecha_creacion']

class ProductoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar productos"""
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'precio', 'stock_actual', 'stock_minimo',
            'categoria_nombre', 'proveedor_nombre', 'activo'
        ]

class ProductoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear productos"""
    class Meta:
        model = Producto
        fields = [
            'nombre', 'descripcion', 'precio', 'stock_actual', 
            'stock_minimo', 'categoria', 'proveedor', 'imagen'
        ] 