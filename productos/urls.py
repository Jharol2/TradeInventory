"""
Configuración de URLs para la aplicación de productos
Este módulo define todas las rutas URL relacionadas con la gestión de productos.

Las URLs incluyen:
- Listado de productos con filtros
- Creación de nuevos productos
- Edición de productos existentes
- Activación/desactivación de productos

Todas las vistas requieren autenticación de usuario.
"""

from django.urls import path
from . import views

# Nombre de la aplicación para evitar conflictos de nombres
app_name = 'productos'

# Configuración de todas las rutas URL de productos
urlpatterns = [
    # URL principal - Lista todos los productos con filtros
    # GET: Muestra la lista de productos
    # Parámetros opcionales: q (búsqueda), categoria, stock, estado, page
    path('', views.lista_productos, name='lista_productos'),
    
    # URL para crear un nuevo producto
    # GET: Muestra formulario vacío
    # POST: Procesa el formulario y crea el producto
    path('crear/', views.crear_producto, name='crear_producto'),
    
    # URL para editar un producto existente
    # GET: Muestra formulario con datos actuales
    # POST: Procesa el formulario y actualiza el producto
    # pk: ID del producto a editar
    path('editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    
    # URL para cambiar el estado de un producto (activo/inactivo)
    # GET: Cambia el estado y redirige a la lista
    # pk: ID del producto cuyo estado se va a cambiar
    path('cambiar-estado/<int:pk>/', views.cambiar_estado_producto, name='cambiar_estado_producto'),
] 