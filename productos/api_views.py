"""
Vistas API para la aplicación de productos
Proporciona endpoints REST para operaciones CRUD de productos
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Producto
from .serializers import (
    ProductoSerializer, 
    ProductoListSerializer, 
    ProductoCreateSerializer
)

class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Producto
    Proporciona operaciones CRUD completas
    """
    queryset = Producto.objects.all()
    # permission_classes = [IsAuthenticated]  # Comentado temporalmente para pruebas
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return ProductoListSerializer
        elif self.action == 'create':
            return ProductoCreateSerializer
        return ProductoSerializer
    
    def get_queryset(self):
        """Filtra el queryset según parámetros de consulta"""
        queryset = Producto.objects.all()
        
        # Filtro por búsqueda
        q = self.request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            )
        
        # Filtro por categoría
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        # Filtro por stock
        stock = self.request.query_params.get('stock', None)
        if stock == 'bajo':
            queryset = queryset.filter(stock_actual__lte=5)
        elif stock == 'normal':
            queryset = queryset.filter(stock_actual__gt=5)
        
        # Filtro por estado
        estado = self.request.query_params.get('estado', 'activo')
        if estado == 'activo':
            queryset = queryset.filter(activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(activo=False)
        
        return queryset.order_by('nombre')
    
    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """Endpoint para obtener productos con stock bajo"""
        productos = self.get_queryset().filter(stock_actual__lte=5)
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Endpoint para cambiar el estado activo/inactivo"""
        producto = self.get_object()
        producto.activo = not producto.activo
        producto.save()
        serializer = self.get_serializer(producto)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def actualizar_stock(self, request, pk=None):
        """Endpoint para actualizar el stock de un producto"""
        producto = self.get_object()
        nueva_cantidad = request.data.get('cantidad')
        
        if nueva_cantidad is None:
            return Response(
                {'error': 'El campo cantidad es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            nueva_cantidad = int(nueva_cantidad)
            producto.stock_actual = nueva_cantidad
            producto.save()
            serializer = self.get_serializer(producto)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'La cantidad debe ser un número entero'}, 
                status=status.HTTP_400_BAD_REQUEST
            ) 