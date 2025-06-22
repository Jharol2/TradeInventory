"""
Sistema de Gestión de Proveedores para TradeInventory
Este módulo maneja todas las operaciones relacionadas con proveedores:

Funcionalidades principales:
- Listado y búsqueda de proveedores
- Creación de nuevos proveedores
- Edición de proveedores existentes
- Activación/desactivación de proveedores

Características:
- Filtros por estado activo/inactivo
- Búsqueda por múltiples campos (nombre, email, teléfono, dirección)
- Validación de formularios
- Mensajes de feedback al usuario
- Autenticación requerida para todas las operaciones
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Proveedor
from .forms import ProveedorForm

@login_required
def lista_proveedores(request):
    """
    Vista principal para listar y filtrar proveedores
    Permite buscar y filtrar proveedores con múltiples criterios
    
    Args:
        request: Objeto HttpRequest con parámetros GET opcionales:
            - estado: Filtro por estado ('activo', 'inactivo', 'todos')
            - q: Término de búsqueda (nombre, email, teléfono, dirección)
            
    Returns:
        HttpResponse: Renderiza la lista de proveedores con filtros aplicados
        
    Funcionalidades:
        - Filtro por estado activo/inactivo
        - Búsqueda por múltiples campos
        - Ordenamiento por nombre alfabético
        - Interfaz de filtros y búsqueda
    """
    # Obtener parámetros de filtrado del request
    estado = request.GET.get('estado', 'activo')  # Por defecto mostrar activos
    query = request.GET.get('q', '')              # Término de búsqueda
    
    # Obtener todos los proveedores de la base de datos
    proveedores_list = Proveedor.objects.all()
    
    # Filtro 1: Por estado del proveedor
    if estado == 'activo':
        proveedores_list = proveedores_list.filter(activo=True)
    elif estado == 'inactivo':
        proveedores_list = proveedores_list.filter(activo=False)
    # Si es 'todos', no se aplica filtro de estado
    
    # Filtro 2: Búsqueda por texto en múltiples campos
    if query:
        proveedores_list = proveedores_list.filter(
            Q(nombre__icontains=query) |      # Buscar en nombre
            Q(email__icontains=query) |       # Buscar en email
            Q(telefono__icontains=query) |    # Buscar en teléfono
            Q(direccion__icontains=query)     # Buscar en dirección
        )
    
    # Ordenar proveedores por nombre alfabéticamente
    proveedores_list = proveedores_list.order_by('nombre')
    
    # Preparar contexto para la plantilla
    context = {
        'proveedores': proveedores_list,
        'estado_actual': estado,
    }
    return render(request, 'proveedores/lista_proveedores.html', context)

@login_required
def crear_proveedor(request):
    """
    Vista para crear un nuevo proveedor
    Maneja el formulario de creación de proveedores con validación
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        
    Returns:
        HttpResponse: Renderiza el formulario o redirige después de crear
        
    Funcionalidades:
        - Muestra formulario vacío en GET
        - Procesa y valida datos en POST
        - Muestra mensajes de éxito/error
        - Redirige a la lista después de crear exitosamente
    """
    if request.method == 'POST':
        # Procesar formulario enviado
        form = ProveedorForm(request.POST)
        if form.is_valid():
            # Guardar el proveedor en la base de datos
            form.save()
            messages.success(request, 'Proveedor creado exitosamente.')
            return redirect('proveedores:lista_proveedores')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario vacío para crear nuevo proveedor
        form = ProveedorForm()
    
    return render(request, 'proveedores/crear_proveedor.html', {'form': form})

@login_required
def editar_proveedor(request, pk):
    """
    Vista para editar un proveedor existente
    Permite modificar los datos de un proveedor específico
    
    Args:
        request: Objeto HttpRequest (GET para mostrar formulario, POST para procesar)
        pk: ID del proveedor a editar
        
    Returns:
        HttpResponse: Renderiza el formulario con datos actuales o redirige después de editar
        
    Funcionalidades:
        - Carga datos existentes del proveedor
        - Permite modificar todos los campos
        - Valida datos antes de guardar
        - Muestra mensajes de éxito/error
    """
    # Obtener el proveedor específico o mostrar error 404 si no existe
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    if request.method == 'POST':
        # Procesar formulario con datos actualizados
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            # Guardar cambios en la base de datos
            form.save()
            messages.success(request, 'Proveedor actualizado exitosamente.')
            return redirect('proveedores:lista_proveedores')
        # Si el formulario no es válido, se mostrará con errores
    else:
        # Mostrar formulario con datos actuales del proveedor
        form = ProveedorForm(instance=proveedor)
    
    return render(request, 'proveedores/crear_proveedor.html', {'form': form})

@login_required
def cambiar_estado_proveedor(request, pk):
    """
    Vista para activar/desactivar un proveedor
    Cambia el estado activo/inactivo de un proveedor específico
    
    Args:
        request: Objeto HttpRequest
        pk: ID del proveedor cuyo estado se va a cambiar
        
    Returns:
        HttpResponseRedirect: Redirige a la lista de proveedores
        
    Funcionalidades:
        - Invierte el estado actual del proveedor
        - Guarda el cambio en la base de datos
        - Muestra mensaje de confirmación
        - Redirige a la lista de proveedores
    """
    # Obtener el proveedor específico o mostrar error 404 si no existe
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    # Invertir el estado actual (activo → inactivo, inactivo → activo)
    proveedor.activo = not proveedor.activo
    proveedor.save()
    
    # Preparar mensaje de confirmación
    estado = "activado" if proveedor.activo else "desactivado"
    messages.success(request, f'Proveedor {estado} exitosamente.')
    
    # Redirigir a la lista de proveedores
    return redirect('proveedores:lista_proveedores')
