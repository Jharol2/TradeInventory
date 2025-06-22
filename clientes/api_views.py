"""
Vistas API para la aplicación de clientes
Proporciona endpoints REST para operaciones CRUD de clientes
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Cliente, Fiado, DetalleFiado
from .serializers import (
    ClienteSerializer, 
    ClienteListSerializer, 
    ClienteCreateSerializer,
    FiadoSerializer,
    DetalleFiadoSerializer
)

class ClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Cliente
    Proporciona operaciones CRUD completas
    """
    queryset = Cliente.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return ClienteListSerializer
        elif self.action == 'create':
            return ClienteCreateSerializer
        return ClienteSerializer
    
    def get_queryset(self):
        """Filtra el queryset según parámetros de consulta"""
        queryset = Cliente.objects.all()
        
        # Filtro por búsqueda
        q = self.request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | 
                Q(apellido__icontains=q) | 
                Q(email__icontains=q)
            )
        
        # Filtro por estado
        estado = self.request.query_params.get('estado', 'activo')
        if estado == 'activo':
            queryset = queryset.filter(activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(activo=False)
        
        return queryset.order_by('nombre', 'apellido')
    
    @action(detail=True, methods=['get'])
    def fiados(self, request, pk=None):
        """Endpoint para obtener fiados de un cliente"""
        cliente = self.get_object()
        fiados = Fiado.objects.filter(cliente=cliente)
        serializer = FiadoSerializer(fiados, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Endpoint para cambiar el estado activo/inactivo"""
        cliente = self.get_object()
        cliente.activo = not cliente.activo
        cliente.save()
        serializer = self.get_serializer(cliente)
        return Response(serializer.data)

class FiadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Fiado
    Proporciona operaciones CRUD completas
    """
    queryset = Fiado.objects.all()
    serializer_class = FiadoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra el queryset según parámetros de consulta"""
        queryset = Fiado.objects.all()
        
        # Filtro por cliente
        cliente_id = self.request.query_params.get('cliente', None)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        return queryset.order_by('-fecha')
    
    @action(detail=True, methods=['post'])
    def abonar(self, request, pk=None):
        """Endpoint para abonar a un fiado"""
        fiado = self.get_object()
        monto = request.data.get('monto')
        
        if monto is None:
            return Response(
                {'error': 'El campo monto es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            monto = float(monto)
            fiado.monto_abonado += monto
            fiado.save()
            serializer = self.get_serializer(fiado)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'El monto debe ser un número válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            ) 