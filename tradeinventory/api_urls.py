"""
URLs para las APIs REST de TradeInventory
Proporciona endpoints REST para todas las aplicaciones
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from productos.api_views import ProductoViewSet
from clientes.api_views import ClienteViewSet, FiadoViewSet
from ventas.api_views import VentaViewSet, DetalleVentaViewSet

# Crear router para las APIs
router = DefaultRouter()

# Registrar ViewSets
router.register(r'productos', ProductoViewSet, basename='api-producto')
router.register(r'clientes', ClienteViewSet, basename='api-cliente')
router.register(r'fiados', FiadoViewSet, basename='api-fiado')
router.register(r'ventas', VentaViewSet, basename='api-venta')
router.register(r'detalles-venta', DetalleVentaViewSet, basename='api-detalle-venta')

# URLs de las APIs
urlpatterns = [
    # Incluir todas las rutas del router
    path('', include(router.urls)),
    
    # Endpoint de autenticación (opcional)
    path('auth/', include('rest_framework.urls')),
] 