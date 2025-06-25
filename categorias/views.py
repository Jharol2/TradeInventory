"""
Sistema de Gestión de Categorías para TradeInventory
Este módulo maneja todas las operaciones relacionadas con categorías de productos:

Funcionalidades principales:
- Listado y búsqueda de categorías
- Creación de nuevas categorías
- Edición de categorías existentes
- Activación/desactivación de categorías
- Detalles de categorías con productos

Características:
- Filtros por estado activo/inactivo
- Búsqueda por nombre y descripción
- Gestión de imágenes de categorías
- Validación de formularios
- Mensajes de feedback al usuario
- Autenticación requerida para todas las operaciones
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from .models import Categoria
from .forms import CategoriaForm
from productos.models import Producto

@login_required
def lista_categorias(request):
    """
    Vista principal para listar y filtrar categorías
    Permite buscar y filtrar categorías con múltiples criterios
    
    Args:
        request: Objeto HttpRequest con parámetros GET opcionales:
            - estado: Filtro por estado ('activo', 'inactivo', 'todos')
            - q: Término de búsqueda (nombre o descripción)
            
    Returns:
        HttpResponse: Renderiza la lista de categorías con filtros aplicados
        
    Funcionalidades:
        - Filtro por estado activo/inactivo
        - Búsqueda por nombre o descripción
        - Ordenamiento por nombre alfabético
        - Interfaz de filtros y búsqueda
    """
    # Obtener parámetros de filtrado del request
    estado = request.GET.get('estado', 'activo')  # Por defecto mostrar activas
    query = request.GET.get('q', '')              # Término de búsqueda
    
    # Obtener todas las categorías de la base de datos
    categorias_list = Categoria.objects.all()
    
    # Filtro 1: Por estado de la categoría
    if estado == 'activo':
        categorias_list = categorias_list.filter(activo=True)
    elif estado == 'inactivo':
        categorias_list = categorias_list.filter(activo=False)
    # Si es 'todos', no se aplica filtro de estado
    
    # Filtro 2: Búsqueda por texto en nombre o descripción
    if query:
        categorias_list = categorias_list.filter(
            Q(nombre__icontains=query) |      # Buscar en nombre (insensible a mayúsculas)
            Q(descripcion__icontains=query)   # Buscar en descripción
        )
    
    # Obtener parámetro de ordenamiento
    orden = request.GET.get('orden', '-fecha_creacion')  # Por defecto más recientes primero
    
    # Manejar ordenamiento especial por número de productos
    if orden in ['productos', '-productos']:
        categorias_list = categorias_list.annotate(
            num_productos=Count('productos')
        ).order_by(orden.replace('productos', 'num_productos'))
    else:
        # Ordenar categorías según el parámetro recibido
        categorias_list = categorias_list.order_by(orden)
    
    # Preparar contexto para la plantilla
    context = {
        'categorias': categorias_list,
        'estado_actual': estado,
    }
    return render(request, 'categorias/lista_categorias.html', context)

@login_required
def crear_categoria(request):
    """
    Vista para crear una nueva categoría
    Maneja el formulario de creación de categorías con validación
    
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
        # Procesar formulario enviado (incluye archivos)
        form = CategoriaForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardar la categoría en la base de datos
            form.save()
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('categorias:lista_categorias')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario vacío para crear nueva categoría
        form = CategoriaForm()
    
    return render(request, 'categorias/crear_categoria.html', {'form': form})

@login_required
def editar_categoria(request, pk):
    """
    Vista para editar una categoría existente
    Permite modificar los datos de una categoría específica
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        pk: ID de la categoría a editar
        
    Returns:
        HttpResponse: Renderiza el formulario con datos actuales o redirige después de editar
        
    Funcionalidades:
        - Carga datos existentes de la categoría
        - Permite modificar todos los campos
        - Maneja archivos de imagen
        - Valida datos antes de guardar
        - Muestra mensajes de éxito/error
    """
    # Obtener la categoría específica o mostrar error 404 si no existe
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        # Procesar formulario con datos actualizados (incluye archivos)
        form = CategoriaForm(request.POST, request.FILES, instance=categoria)
        if form.is_valid():
            # Guardar cambios en la base de datos
            form.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('categorias:lista_categorias')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario con datos actuales de la categoría
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'categorias/crear_categoria.html', {'form': form})

@login_required
def cambiar_estado(request, pk):
    """
    Vista para activar/desactivar una categoría
    Cambia el estado activo/inactivo de una categoría específica
    
    Args:
        request: Objeto HttpRequest
        pk: ID de la categoría cuyo estado se va a cambiar
        
    Returns:
        HttpResponseRedirect: Redirige a la lista de categorías
        
    Funcionalidades:
        - Invierte el estado actual de la categoría
        - Guarda el cambio en la base de datos
        - Muestra mensaje de confirmación
        - Redirige a la lista de categorías
    """
    # Obtener la categoría específica o mostrar error 404 si no existe
    categoria = get_object_or_404(Categoria, pk=pk)
    
    # Invertir el estado actual (activo → inactivo, inactivo → activo)
    categoria.activo = not categoria.activo
    categoria.save()
    
    # Preparar mensaje de confirmación
    estado = "activada" if categoria.activo else "desactivada"
    messages.success(request, f'Categoría {estado} exitosamente.')
    
    # Redirigir a la lista de categorías
    return redirect('categorias:lista_categorias')

@login_required
def detalle_categoria(request, pk):
    """
    Vista para mostrar detalles de una categoría específica
    Muestra información de la categoría y lista todos sus productos
    
    Args:
        request: Objeto HttpRequest
        pk: ID de la categoría a mostrar
        
    Returns:
        HttpResponse: Renderiza el detalle de la categoría
        
    Funcionalidades:
        - Muestra información de la categoría
        - Lista todos los productos activos de la categoría
        - Ordena productos por nombre
        - Proporciona vista detallada de la categoría
    """
    # Obtener la categoría específica o mostrar error 404 si no existe
    categoria = get_object_or_404(Categoria, pk=pk)
    
    # Obtener todos los productos activos de esta categoría
    productos = Producto.objects.filter(categoria=categoria, activo=True).order_by('nombre')
    
    # Preparar contexto para la plantilla
    context = {
        'categoria': categoria,
        'productos': productos,
    }
    return render(request, 'categorias/detalle_categoria.html', context)
