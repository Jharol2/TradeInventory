"""
Vistas para la gestión de productos en TradeInventory
Este módulo maneja todas las operaciones relacionadas con productos:
- Listado y búsqueda de productos
- Creación de nuevos productos
- Edición de productos existentes
- Activación/desactivación de productos

Características:
- Filtros avanzados (nombre, categoría, stock, estado)
- Paginación para mejor rendimiento
- Validación de formularios
- Mensajes de feedback al usuario
- Autenticación requerida para todas las operaciones
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Producto
from categorias.models import Categoria
from .forms import ProductoForm

@login_required
def lista_productos(request):
    """
    Vista principal para listar y filtrar productos
    Permite buscar, filtrar y paginar productos con múltiples criterios
    
    Args:
        request: Objeto HttpRequest con parámetros GET opcionales:
            - q: Término de búsqueda (nombre o descripción)
            - categoria: ID de categoría para filtrar
            - stock: Filtro de stock ('bajo' para ≤5, 'normal' para >5)
            - estado: Estado del producto ('activo', 'inactivo', 'todos')
            - page: Número de página para paginación
            
    Returns:
        HttpResponse: Renderiza la lista de productos con filtros aplicados
        
    Funcionalidades:
        - Búsqueda por nombre o descripción
        - Filtro por categoría
        - Filtro por nivel de stock
        - Filtro por estado (activo/inactivo)
        - Paginación (12 productos por página)
        - Ordenamiento por nombre
    """
    # Obtener todos los productos de la base de datos
    productos_list = Producto.objects.all()
    
    # Aplicar filtros según los parámetros recibidos
    query = request.GET.get('q')
    categoria_id = request.GET.get('categoria')
    stock_filter = request.GET.get('stock')
    estado = request.GET.get('estado', 'activo')  # Por defecto mostrar activos
    
    # Filtro 1: Búsqueda por texto (nombre o descripción)
    if query:
        productos_list = productos_list.filter(
            Q(nombre__icontains=query) |  # Buscar en nombre (insensible a mayúsculas)
            Q(descripcion__icontains=query)  # Buscar en descripción
        )
    
    # Filtro 2: Por categoría específica
    if categoria_id:
        productos_list = productos_list.filter(categoria_id=categoria_id)
    
    # Filtro 3: Por nivel de stock
    if stock_filter == 'bajo':
        productos_list = productos_list.filter(stock_actual__lte=5)  # Stock bajo (≤5)
    elif stock_filter == 'normal':
        productos_list = productos_list.filter(stock_actual__gt=5)   # Stock normal (>5)
    
    # Filtro 4: Por estado del producto
    if estado == 'activo':
        productos_list = productos_list.filter(activo=True)
    elif estado == 'inactivo':
        productos_list = productos_list.filter(activo=False)
    # Si es 'todos', no se aplica filtro de estado
    
    # Obtener parámetro de ordenamiento
    orden = request.GET.get('orden', '-fecha_creacion')  # Por defecto más recientes primero
    
    # Ordenar productos según el parámetro recibido
    productos_list = productos_list.order_by(orden)
    
    # Configurar paginación para mejorar rendimiento
    paginator = Paginator(productos_list, 12)  # 12 productos por página
    page = request.GET.get('page')
    productos = paginator.get_page(page)
    
    # Obtener todas las categorías activas para el filtro de categorías
    categorias = Categoria.objects.filter(activo=True)
    
    # Preparar contexto para la plantilla
    context = {
        'productos': productos,
        'categorias': categorias,
        'estado_actual': estado,
    }
    
    return render(request, 'productos/lista_productos.html', context)

@login_required
def crear_producto(request):
    """
    Vista para crear un nuevo producto
    Maneja el formulario de creación de productos con validación
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de crear
        
    Funcionalidades:
        - Muestra formulario vacío en GET
        - Procesa y valida datos en POST
        - Maneja archivos de imagen subidos
        - Muestra mensajes de éxito/error
        - Redirige a la lista después de crear exitosamente
    """
    if request.method == 'POST':
        # Procesar formulario enviado
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardar el producto en la base de datos
            producto = form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('productos:lista_productos')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario vacío para crear nuevo producto
        form = ProductoForm()
    
    return render(request, 'productos/crear_producto.html', {'form': form})

@login_required
def editar_producto(request, pk):
    """
    Vista para editar un producto existente
    Permite modificar los datos de un producto específico
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        pk: ID del producto a editar
        
    Returns:
        HttpResponse: Renderiza el formulario con datos actuales o redirige después de editar
        
    Funcionalidades:
        - Carga datos existentes del producto
        - Permite modificar todos los campos
        - Maneja archivos de imagen
        - Valida datos antes de guardar
        - Muestra mensajes de éxito/error
    """
    # Obtener el producto específico o mostrar error 404 si no existe
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        # Procesar formulario con datos actualizados
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            # Guardar cambios en la base de datos
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('productos:lista_productos')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario con datos actuales del producto
        form = ProductoForm(instance=producto)
    
    # Preparar contexto con formulario y datos del producto
    return render(request, 'productos/editar_producto.html', {
        'form': form,
        'producto': producto
    })

@login_required
def cambiar_estado_producto(request, pk):
    """
    Vista para activar/desactivar un producto
    Cambia el estado activo/inactivo de un producto específico
    
    Args:
        request: Objeto HttpRequest
        pk: ID del producto cuyo estado se va a cambiar
        
    Returns:
        HttpResponseRedirect: Redirige a la lista de productos
        
    Funcionalidades:
        - Invierte el estado actual del producto
        - Guarda el cambio en la base de datos
        - Muestra mensaje de confirmación
        - Redirige a la lista de productos
    """
    # Obtener el producto específico o mostrar error 404 si no existe
    producto = get_object_or_404(Producto, pk=pk)
    
    # Invertir el estado actual (activo → inactivo, inactivo → activo)
    producto.activo = not producto.activo
    producto.save()
    
    # Preparar mensaje de confirmación
    estado = "activado" if producto.activo else "desactivado"
    messages.success(request, f'Producto {estado} exitosamente.')
    
    # Redirigir a la lista de productos
    return redirect('productos:lista_productos')
