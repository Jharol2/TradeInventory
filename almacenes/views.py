from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Almacen

@login_required
def lista_almacenes(request):
    # Obtener el filtro de estado y la búsqueda
    estado = request.GET.get('estado', 'Activo')
    busqueda = request.GET.get('busqueda', '')
    
    # Filtrar almacenes según el estado
    almacenes = Almacen.objects.all()
    if estado == 'Activo':
        almacenes = almacenes.filter(activo=True)
    elif estado == 'Inactivo':
        almacenes = almacenes.filter(activo=False)
    
    # Aplicar búsqueda si existe
    if busqueda:
        almacenes = almacenes.filter(
            Q(nombre__icontains=busqueda) |
            Q(direccion__icontains=busqueda)
        )
    
    context = {
        'almacenes': almacenes,
        'estado_actual': estado,
        'busqueda': busqueda,
    }
    return render(request, 'almacenes/lista_almacenes.html', context)

@login_required
def crear_almacen(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        
        try:
            almacen = Almacen.objects.create(
                nombre=nombre,
                direccion=direccion,
                activo=True  # Por defecto, los almacenes nuevos están activos
            )
            messages.success(request, 'Almacén creado exitosamente.')
            return redirect('almacenes:lista_almacenes')
        except Exception as e:
            messages.error(request, f'Error al crear el almacén: {str(e)}')
    
    return render(request, 'almacenes/crear_almacen.html')

@login_required
def editar_almacen(request, pk):
    almacen = get_object_or_404(Almacen, pk=pk)
    
    if request.method == 'POST':
        almacen.nombre = request.POST.get('nombre')
        almacen.direccion = request.POST.get('direccion')
        
        try:
            almacen.save()
            messages.success(request, 'Almacén actualizado exitosamente.')
            return redirect('almacenes:lista_almacenes')
        except Exception as e:
            messages.error(request, f'Error al actualizar el almacén: {str(e)}')
    
    return render(request, 'almacenes/editar_almacen.html', {
        'almacen': almacen
    })

@login_required
def cambiar_estado_almacen(request, pk):
    almacen = get_object_or_404(Almacen, pk=pk)
    almacen.activo = not almacen.activo
    almacen.save()
    estado = "activado" if almacen.activo else "desactivado"
    messages.success(request, f'Almacén {estado} exitosamente.')
    return redirect('almacenes:lista_almacenes')
