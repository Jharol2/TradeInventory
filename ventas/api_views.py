"""
Vistas API para la aplicación de ventas
Proporciona endpoints REST para operaciones CRUD de ventas
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Venta, DetalleVenta
from .serializers import (
    VentaSerializer, 
    VentaListSerializer, 
    VentaCreateSerializer,
    DetalleVentaSerializer
)

class VentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo Venta
    Proporciona operaciones CRUD completas
    """
    queryset = Venta.objects.all()
    # permission_classes = [IsAuthenticated]  # Comentado temporalmente para pruebas
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return VentaListSerializer
        elif self.action == 'create':
            return VentaCreateSerializer
        return VentaSerializer
    
    def get_queryset(self):
        """Filtra el queryset según parámetros de consulta"""
        queryset = Venta.objects.all()
        
        # Filtro por cliente
        cliente_id = self.request.query_params.get('cliente', None)
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        # Filtro por tipo de venta
        es_fiado = self.request.query_params.get('es_fiado', None)
        if es_fiado is not None:
            es_fiado = es_fiado.lower() == 'true'
            queryset = queryset.filter(es_fiado=es_fiado)
        
        # Filtro por estado
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por fecha
        fecha = self.request.query_params.get('fecha', None)
        if fecha:
            queryset = queryset.filter(fecha__date=fecha)
        
        return queryset.order_by('-fecha')
    
    @action(detail=False, methods=['get'])
    def ventas_hoy(self, request):
        """Endpoint para obtener ventas del día actual"""
        hoy = timezone.now().date()
        ventas = self.get_queryset().filter(fecha__date=hoy)
        total = ventas.aggregate(total=Sum('total'))['total'] or 0
        
        serializer = self.get_serializer(ventas, many=True)
        return Response({
            'ventas': serializer.data,
            'total_hoy': total,
            'fecha': hoy
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Endpoint para obtener estadísticas de ventas"""
        hoy = timezone.now().date()
        
        # Ventas del día
        ventas_hoy = self.get_queryset().filter(fecha__date=hoy)
        total_hoy = ventas_hoy.aggregate(total=Sum('total'))['total'] or 0
        
        # Ventas normales vs fiado
        ventas_normales = ventas_hoy.filter(es_fiado=False).count()
        ventas_fiado = ventas_hoy.filter(es_fiado=True).count()
        
        # Total de ventas
        total_ventas = self.get_queryset().aggregate(total=Sum('total'))['total'] or 0
        
        return Response({
            'total_hoy': total_hoy,
            'ventas_hoy': ventas_hoy.count(),
            'ventas_normales_hoy': ventas_normales,
            'ventas_fiado_hoy': ventas_fiado,
            'total_general': total_ventas
        })
    
    @action(detail=True, methods=['post'])
    def abonar(self, request, pk=None):
        """Endpoint para abonar a una venta a fiado"""
        venta = self.get_object()
        
        if not venta.es_fiado:
            return Response(
                {'error': 'Solo se puede abonar a ventas a fiado'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        monto = request.data.get('monto')
        if monto is None:
            return Response(
                {'error': 'El campo monto es requerido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            monto = float(monto)
            venta.monto_abonado += monto
            venta.fecha_ultimo_abono = timezone.now()
            venta.save()
            serializer = self.get_serializer(venta)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'El monto debe ser un número válido'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class DetalleVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el modelo DetalleVenta
    Proporciona operaciones CRUD completas
    """
    queryset = DetalleVenta.objects.all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtra el queryset según parámetros de consulta"""
        queryset = DetalleVenta.objects.all()
        
        # Filtro por venta
        venta_id = self.request.query_params.get('venta', None)
        if venta_id:
            queryset = queryset.filter(venta_id=venta_id)
        
        # Filtro por producto
        producto_id = self.request.query_params.get('producto', None)
        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        
        return queryset.order_by('-id') 