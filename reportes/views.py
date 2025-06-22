"""
Sistema de Reportes Profesionales para TradeInventory
Este módulo contiene todas las vistas relacionadas con la generación de reportes
del sistema de gestión de inventario.

Funcionalidades principales:
- Reporte de productos (stock, ventas, rotación)
- Reporte de ventas (análisis temporal, productos top)
- Reporte de clientes (comportamiento de compra)
- Reporte de proveedores (rendimiento, análisis de productos)
- Reporte de fiados (gestión de deudas pendientes)
- Reporte de categorías (análisis de rendimiento por categoría)

Características:
- Filtros por fecha personalizables
- Exportación a Excel con formato profesional
- Métricas avanzadas y análisis de tendencias
- Interfaz web responsive
- Autenticación requerida para todos los reportes
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Avg, Max, Min, Q, F, ExpressionWrapper, DecimalField, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta
import io
import xlsxwriter
from decimal import Decimal

from productos.models import Producto
from ventas.models import Venta, DetalleVenta
from clientes.models import Cliente, Fiado, DetalleFiado
from proveedores.models import Proveedor
from categorias.models import Categoria

@login_required
def lista_reportes(request):
    """
    Vista principal del menú de reportes
    Muestra la página con enlaces a todos los reportes disponibles
    
    Args:
        request: Objeto HttpRequest de Django
        
    Returns:
        HttpResponse: Renderiza la página de lista de reportes
    """
    return render(request, 'reportes/lista_reportes.html')

@login_required
def reporte_productos(request):
    """
    Reporte completo de análisis de productos
    Genera estadísticas detalladas sobre productos, stock y ventas
    
    Args:
        request: Objeto HttpRequest de Django con parámetros GET opcionales:
            - fecha_inicio: Fecha de inicio para el análisis (formato YYYY-MM-DD)
            - fecha_fin: Fecha de fin para el análisis (formato YYYY-MM-DD)
            - formato: Si es 'excel', exporta a Excel en lugar de mostrar en web
            
    Returns:
        HttpResponse: Renderiza el reporte web o devuelve archivo Excel
        
    Análisis incluidos:
        - Productos con stock bajo (≤ stock mínimo)
        - Productos más vendidos en el período
        - Análisis de rotación de inventario
    """
    # Obtener parámetros de fecha del request
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Procesar fechas: si no se proporcionan, usar últimos 30 días
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Análisis 1: Productos con stock bajo
    # Filtra productos donde el stock actual es menor o igual al stock mínimo
    productos_bajo_stock = Producto.objects.filter(
        stock_actual__lte=F('stock_minimo')
    ).select_related('categoria', 'proveedor').order_by('stock_actual')
    
    # Análisis 2: Productos más vendidos en el período
    # Calcula total vendido e ingresos por producto en el rango de fechas
    productos_mas_vendidos = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'producto__nombre',
        'producto__categoria__nombre',
        'producto__proveedor__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:10]  # Top 10 productos
    
    # Análisis 3: Rotación de inventario
    # Calcula qué productos tienen mejor rotación (más ventas vs stock actual)
    productos_rotacion = Producto.objects.filter(
        detalleventa__venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'nombre',
        'categoria__nombre',
        'stock_actual'
    ).annotate(
        unidades_vendidas=Sum('detalleventa__cantidad'),
        valor_vendido=Sum(F('detalleventa__cantidad') * F('detalleventa__precio_unitario'))
    ).order_by('-unidades_vendidas')[:10]  # Top 10 por rotación
    
    # Verificar si se solicita exportación a Excel
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_productos_excel(
            request,
            productos_bajo_stock,
            productos_mas_vendidos,
            productos_rotacion,
            fecha_inicio,
            fecha_fin
        )
    
    # Preparar contexto para la plantilla web
    context = {
        'productos_bajo_stock': productos_bajo_stock,
        'productos_mas_vendidos': productos_mas_vendidos,
        'productos_rotacion': productos_rotacion,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/reporte_productos.html', context)

@login_required
def reporte_ventas(request):
    """
    Reporte de análisis de ventas
    Genera estadísticas detalladas sobre el comportamiento de ventas
    
    Args:
        request: Objeto HttpRequest de Django con parámetros GET opcionales:
            - fecha_inicio: Fecha de inicio para el análisis
            - fecha_fin: Fecha de fin para el análisis
            - formato: Si es 'excel', exporta a Excel
            
    Returns:
        HttpResponse: Renderiza el reporte web o devuelve archivo Excel
        
    Análisis incluidos:
        - Ventas por día (conteo, monto total, promedio)
        - Ventas por mes (agregación mensual)
        - Productos top (más vendidos en el período)
    """
    # Obtener y procesar parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Análisis 1: Ventas por día
    # Agrupa ventas por fecha y calcula métricas diarias
    ventas_por_dia = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin)
    ).values('fecha').annotate(
        total_ventas=Count('id'),
        monto_total=Sum('total'),
        promedio_venta=Avg('total')
    ).order_by('fecha')
    
    # Análisis 2: Ventas por mes
    # Agrupa ventas por mes y año para análisis temporal
    ventas_por_mes = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin)
    ).extra(
        select={'mes': "EXTRACT(month FROM fecha)", 'año': "EXTRACT(year FROM fecha)"}
    ).values('mes', 'año').annotate(
        total_ventas=Count('id'),
        monto_total=Sum('total'),
        promedio_venta=Avg('total')
    ).order_by('año', 'mes')
    
    # Análisis 3: Productos top en ventas
    # Identifica los productos más vendidos en el período
    productos_top = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'producto__nombre',
        'producto__categoria__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:10]  # Top 10 productos
    
    # Verificar exportación a Excel
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_ventas_excel(
            request,
            ventas_por_dia,
            ventas_por_mes,
            productos_top,
            fecha_inicio,
            fecha_fin
        )
    
    # Preparar contexto para la plantilla
    context = {
        'ventas_por_dia': ventas_por_dia,
        'ventas_por_mes': ventas_por_mes,
        'productos_top': productos_top,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/reporte_ventas.html', context)

@login_required
def reporte_clientes(request):
    """
    Reporte de análisis de clientes
    Genera estadísticas sobre el comportamiento de compra de los clientes
    
    Args:
        request: Objeto HttpRequest de Django con parámetros GET opcionales:
            - fecha_inicio: Fecha de inicio para el análisis
            - fecha_fin: Fecha de fin para el análisis
            - formato: Si es 'excel', exporta a Excel
            
    Returns:
        HttpResponse: Renderiza el reporte web o devuelve archivo Excel
        
    Análisis incluidos:
        - Clientes top por monto total de compras
        - Métricas por cliente (frecuencia, promedio, última compra)
    """
    # Obtener y procesar parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Análisis: Clientes top por monto total de compras
    # Calcula métricas detalladas por cliente en el período
    clientes_top = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin),
        cliente__isnull=False  # Solo ventas con cliente asociado
    ).values(
        'cliente__nombre',
        'cliente__documento'
    ).annotate(
        total_compras=Count('id'),
        monto_total=Sum('total'),
        promedio_compra=Avg('total'),
        ultima_compra=Max('fecha')
    ).order_by('-monto_total')[:10]  # Top 10 clientes
    
    # Verificar exportación a Excel
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_clientes_excel(
            request,
            clientes_top,
            fecha_inicio,
            fecha_fin
        )
    
    # Preparar contexto para la plantilla
    context = {
        'clientes_top': clientes_top,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/reporte_clientes.html', context)

@login_required
def reporte_proveedores(request):
    """
    Reporte de análisis de proveedores
    Genera estadísticas sobre el rendimiento de los proveedores
    
    Args:
        request: Objeto HttpRequest de Django con parámetros GET opcionales:
            - fecha_inicio: Fecha de inicio para el análisis
            - fecha_fin: Fecha de fin para el análisis
            - formato: Si es 'excel', exporta a Excel
            
    Returns:
        HttpResponse: Renderiza el reporte web o devuelve archivo Excel
        
    Análisis incluidos:
        - Rendimiento por proveedor (productos vendidos, ingresos)
        - Análisis de márgenes por proveedor
        - Productos más vendidos por proveedor
    """
    # Obtener y procesar parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Análisis de proveedores por productos vendidos con métricas mejoradas
    proveedores_analisis = Producto.objects.filter(
        proveedor__isnull=False,
        detalleventa__venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'proveedor__nombre',
        'proveedor__id'
    ).annotate(
        total_productos=Count('id', distinct=True),
        total_vendido=Sum('detalleventa__cantidad'),
        total_ingresos=Sum(F('detalleventa__cantidad') * F('detalleventa__precio_unitario')),
        costo_total=Sum(F('detalleventa__cantidad') * F('precio')),
        margen_ganancia=ExpressionWrapper(
            Sum(F('detalleventa__cantidad') * F('detalleventa__precio_unitario')) - 
            Sum(F('detalleventa__cantidad') * F('precio')),
            output_field=DecimalField()
        ),
        ultima_venta=Max('detalleventa__venta__fecha')
    ).order_by('-total_ingresos')
    
    # Calcular porcentaje de margen después de la consulta
    for proveedor in proveedores_analisis:
        if proveedor['total_ingresos'] and proveedor['total_ingresos'] > 0:
            proveedor['porcentaje_margen'] = (proveedor['margen_ganancia'] / proveedor['total_ingresos']) * 100
        else:
            proveedor['porcentaje_margen'] = 0
    
    # Productos por proveedor con información de inventario mejorada
    productos_por_proveedor = Producto.objects.filter(
        proveedor__isnull=False
    ).values(
        'proveedor__nombre',
        'proveedor__id'
    ).annotate(
        cantidad_productos=Count('id'),
        stock_total=Sum('stock_actual'),
        valor_inventario=Sum(F('stock_actual') * F('precio')),
        productos_sin_stock=Count('id', filter=Q(stock_actual=0)),
        ultima_venta=Max('detalleventa__venta__fecha')
    ).order_by('-cantidad_productos')
    
    # Calcular productos bajo stock después de la consulta para mayor precisión
    for proveedor in productos_por_proveedor:
        # Obtener todos los productos de este proveedor
        productos_proveedor = Producto.objects.filter(
            proveedor_id=proveedor['proveedor__id']
        )
        
        bajo_stock_count = 0
        for producto in productos_proveedor:
            stock_minimo = producto.stock_minimo if producto.stock_minimo is not None else 5
            if producto.stock_actual <= stock_minimo:
                bajo_stock_count += 1
        
        proveedor['productos_bajo_stock'] = bajo_stock_count
    
    # Proveedores con mejor margen (solo los que tienen ventas)
    proveedores_margen = Producto.objects.filter(
        proveedor__isnull=False,
        detalleventa__venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'proveedor__nombre',
        'proveedor__id'
    ).annotate(
        total_ventas=Sum('detalleventa__cantidad'),
        ingresos_totales=Sum(F('detalleventa__cantidad') * F('detalleventa__precio_unitario')),
        costos_totales=Sum(F('detalleventa__cantidad') * F('precio'))
    ).filter(total_ventas__gt=0)
    
    # Calcular margen promedio después de la consulta
    for proveedor in proveedores_margen:
        if proveedor['ingresos_totales'] and proveedor['ingresos_totales'] > 0:
            margen_absoluto = proveedor['ingresos_totales'] - proveedor['costos_totales']
            proveedor['margen_promedio'] = (margen_absoluto / proveedor['ingresos_totales']) * 100
        else:
            proveedor['margen_promedio'] = 0
    
    # Ordenar por margen promedio
    proveedores_margen = sorted(proveedores_margen, key=lambda x: x['margen_promedio'], reverse=True)
    
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_proveedores_excel(
            request,
            proveedores_analisis,
            productos_por_proveedor,
            proveedores_margen,
            fecha_inicio,
            fecha_fin
        )
    
    context = {
        'proveedores_analisis': proveedores_analisis,
        'productos_por_proveedor': productos_por_proveedor,
        'proveedores_margen': proveedores_margen,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/reporte_proveedores.html', context)

@login_required
def reporte_fiados(request):
    """Reporte de fiados y deudas pendientes"""
    from clientes.models import Cliente, Fiado, DetalleFiado
    
    # Obtener parámetros de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    else:
        fecha_inicio = timezone.now().date() - timedelta(days=30)
    
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        fecha_fin = timezone.now().date()
    
    # Obtener fiados pendientes
    fiados_pendientes = Fiado.objects.filter(
        fecha__date__range=[fecha_inicio, fecha_fin],
        pagado=False
    ).select_related('cliente').order_by('-fecha')
    
    # Calcular días vencidos para cada fiado
    for fiado in fiados_pendientes:
        fiado.dias_vencido = (timezone.now().date() - fiado.fecha.date()).days
    
    # Estadísticas de clientes con fiados
    clientes_fiados = Cliente.objects.filter(
        fiados__pagado=False,
        fiados__fecha__date__range=[fecha_inicio, fecha_fin]
    ).annotate(
        total_fiado=Sum('fiados__monto'),
        cantidad_fiados=Count('fiados')
    ).filter(total_fiado__gt=0).order_by('-total_fiado')
    
    # Calcular margen promedio después de la consulta
    for cliente in clientes_fiados:
        if cliente.cantidad_fiados > 0:
            cliente.promedio_fiado = cliente.total_fiado / cliente.cantidad_fiados
        else:
            cliente.promedio_fiado = 0
    
    # Análisis por antigüedad de deudas
    fiados_antiguedad = Fiado.objects.filter(
        pagado=False
    ).annotate(
        dias_vencido=ExpressionWrapper(
            timezone.now().date() - F('fecha__date'),
            output_field=IntegerField()
        )
    ).values('dias_vencido').annotate(
        cantidad=Count('id'),
        monto_total=Sum('monto')
    ).order_by('dias_vencido')
    
    # Productos más fiados (solo pendientes para la vista web)
    productos_fiados = DetalleFiado.objects.filter(
        fiado__pagado=False,
        fiado__fecha__date__range=[fecha_inicio, fecha_fin]
    ).values(
        'producto__nombre',
        'producto__categoria__nombre'
    ).annotate(
        total_cantidad=Sum('cantidad'),
        total_valor=Sum('subtotal'),
        cantidad_fiados=Count('fiado', distinct=True)
    ).order_by('-total_valor')[:10]
    
    # TODOS los detalles de fiados para el Excel (incluyendo cancelados, pagados, etc.)
    todos_detalles_fiados = DetalleFiado.objects.filter(
        fiado__fecha__date__range=[fecha_inicio, fecha_fin]
    ).select_related('fiado', 'fiado__cliente', 'producto').order_by('-fiado__fecha')
    
    # Totales
    total_fiado_pendiente = fiados_pendientes.aggregate(
        total=Sum('monto')
    )['total'] or 0
    
    total_clientes_fiados = clientes_fiados.count()
    
    context = {
        'fiados_pendientes': fiados_pendientes,
        'clientes_fiados': clientes_fiados,
        'fiados_antiguedad': fiados_antiguedad,
        'productos_fiados': productos_fiados,
        'total_fiado_pendiente': total_fiado_pendiente,
        'total_clientes_fiados': total_clientes_fiados,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    # Exportar a Excel si se solicita
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_fiados_excel(
            request, fiados_pendientes, clientes_fiados, 
            fiados_antiguedad, productos_fiados, todos_detalles_fiados, fecha_inicio, fecha_fin
        )
    
    return render(request, 'reportes/reporte_fiados.html', context)

@login_required
def cambiar_estado_fiado(request, fiado_id):
    """Cambiar el estado de un fiado (pagado/cancelado)"""
    from clientes.models import Fiado
    from django.utils import timezone
    from django.contrib import messages
    from django.shortcuts import redirect
    
    try:
        fiado = Fiado.objects.get(id=fiado_id)
        accion = request.POST.get('accion')
        
        if accion == 'pagar':
            fiado.pagado = True
            fiado.fecha_pago = timezone.now()
            fiado.save()
            messages.success(request, f'Fiado de {fiado.cliente.nombre} marcado como PAGADO')
        elif accion == 'cancelar':
            fiado.pagado = True  # También marcamos como pagado para "cancelar"
            fiado.fecha_pago = timezone.now()
            fiado.save()
            messages.warning(request, f'Fiado de {fiado.cliente.nombre} marcado como CANCELADO')
        else:
            messages.error(request, 'Acción no válida')
            
    except Fiado.DoesNotExist:
        messages.error(request, 'Fiado no encontrado')
    except Exception as e:
        messages.error(request, f'Error al cambiar estado: {str(e)}')
    
    # Redirigir de vuelta al reporte de fiados
    return redirect('reportes:reporte_fiados')

@login_required
def detalle_fiado(request, fiado_id):
    """Mostrar detalles de un fiado específico"""
    from clientes.models import Fiado, DetalleFiado
    
    try:
        fiado = Fiado.objects.select_related('cliente').get(id=fiado_id)
        detalles = DetalleFiado.objects.filter(fiado=fiado).select_related('producto')
        
        context = {
            'fiado': fiado,
            'detalles': detalles,
        }
        
        return render(request, 'reportes/detalle_fiado.html', context)
        
    except Fiado.DoesNotExist:
        messages.error(request, 'Fiado no encontrado')
        return redirect('reportes:reporte_fiados')

def exportar_reporte_proveedores_excel(request, proveedores_analisis, productos_por_proveedor, proveedores_margen, fecha_inicio, fecha_fin):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})
    
    # Formato para títulos
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#2E86AB',
        'font_color': 'white',
        'border': 1,
        'align': 'center'
    })
    
    # Formato para subtítulos
    subheader_format = workbook.add_format({
        'bold': True,
        'bg_color': '#A23B72',
        'font_color': 'white',
        'border': 1,
        'align': 'center'
    })
    
    # Formato para números
    number_format = workbook.add_format({'num_format': '#,##0.00'})
    
    # Formato para porcentajes
    percent_format = workbook.add_format({'num_format': '0.00%'})
    
    # Formato para fechas
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # ===== HOJA 1: ANÁLISIS DE PROVEEDORES POR PRODUCTOS VENDIDOS =====
    worksheet_analisis = workbook.add_worksheet('Análisis de Proveedores')
    worksheet_analisis.set_column('A:A', 25)
    worksheet_analisis.set_column('B:B', 10)
    worksheet_analisis.set_column('C:C', 15)
    worksheet_analisis.set_column('D:D', 15)
    worksheet_analisis.set_column('E:E', 15)
    worksheet_analisis.set_column('F:F', 15)
    worksheet_analisis.set_column('G:G', 15)
    worksheet_analisis.set_column('H:H', 15)
    worksheet_analisis.set_column('I:I', 15)
    
    worksheet_analisis.merge_range('A1:I1', 'ANÁLISIS DE PROVEEDORES POR PRODUCTOS VENDIDOS', header_format)
    worksheet_analisis.merge_range('A2:I2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Proveedor', 'ID', 'Total Productos', 'Total Vendido', 'Total Ingresos', 'Costo Total', 'Margen de Ganancia', '% Margen', 'Última Venta']
    for col, header in enumerate(headers):
        worksheet_analisis.write(3, col, header, header_format)
    
    row = 4
    for proveedor in proveedores_analisis:
        worksheet_analisis.write(row, 0, proveedor['proveedor__nombre'])
        worksheet_analisis.write(row, 1, proveedor['proveedor__id'])
        worksheet_analisis.write(row, 2, proveedor['total_productos'])
        worksheet_analisis.write(row, 3, proveedor['total_vendido'])
        worksheet_analisis.write(row, 4, float(proveedor['total_ingresos']), number_format)
        worksheet_analisis.write(row, 5, float(proveedor['costo_total']), number_format)
        worksheet_analisis.write(row, 6, float(proveedor['margen_ganancia']), number_format)
        worksheet_analisis.write(row, 7, float(proveedor['porcentaje_margen']) / 100, percent_format)
        if proveedor['ultima_venta']:
            # Convertir a datetime sin timezone
            ultima_venta = proveedor['ultima_venta']
            if hasattr(ultima_venta, 'replace'):
                ultima_venta = ultima_venta.replace(tzinfo=None)
            worksheet_analisis.write(row, 8, ultima_venta, date_format)
        else:
            worksheet_analisis.write(row, 8, 'Sin ventas')
        row += 1
    
    # ===== HOJA 2: INVENTARIO POR PROVEEDOR =====
    worksheet_productos = workbook.add_worksheet('Inventario por Proveedor')
    worksheet_productos.set_column('A:A', 25)
    worksheet_productos.set_column('B:B', 15)
    worksheet_productos.set_column('C:C', 15)
    worksheet_productos.set_column('D:D', 15)
    worksheet_productos.set_column('E:E', 15)
    worksheet_productos.set_column('F:F', 15)
    worksheet_productos.set_column('G:G', 15)
    
    worksheet_productos.merge_range('A1:G1', 'INVENTARIO POR PROVEEDOR', header_format)
    worksheet_productos.merge_range('A2:G2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Proveedor', 'Cantidad Productos', 'Stock Total', 'Valor Inventario', 'Productos Bajo Stock', 'Productos Sin Stock', 'Última Venta']
    for col, header in enumerate(headers):
        worksheet_productos.write(3, col, header, header_format)
    
    row = 4
    for proveedor in productos_por_proveedor:
        worksheet_productos.write(row, 0, proveedor['proveedor__nombre'])
        worksheet_productos.write(row, 1, proveedor['cantidad_productos'])
        worksheet_productos.write(row, 2, float(proveedor['stock_total']), number_format)
        worksheet_productos.write(row, 3, float(proveedor['valor_inventario']), number_format)
        worksheet_productos.write(row, 4, proveedor['productos_bajo_stock'])
        worksheet_productos.write(row, 5, proveedor['productos_sin_stock'])
        if proveedor['ultima_venta']:
            # Convertir a datetime sin timezone
            ultima_venta = proveedor['ultima_venta']
            if hasattr(ultima_venta, 'replace'):
                ultima_venta = ultima_venta.replace(tzinfo=None)
            worksheet_productos.write(row, 6, ultima_venta, date_format)
        else:
            worksheet_productos.write(row, 6, 'Sin ventas')
        row += 1
    
    # ===== HOJA 3: PROVEEDORES CON MEJOR MARGEN =====
    worksheet_margen = workbook.add_worksheet('Proveedores con Mejor Margen')
    worksheet_margen.set_column('A:A', 25)
    worksheet_margen.set_column('B:B', 15)
    worksheet_margen.set_column('C:C', 15)
    worksheet_margen.set_column('D:D', 15)
    
    worksheet_margen.merge_range('A1:D1', 'PROVEEDORES CON MEJOR MARGEN', header_format)
    worksheet_margen.merge_range('A2:D2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Proveedor', 'Margen Promedio', 'Total Ventas', 'Ingresos Totales']
    for col, header in enumerate(headers):
        worksheet_margen.write(3, col, header, header_format)
    
    row = 4
    for proveedor in proveedores_margen:
        worksheet_margen.write(row, 0, proveedor['proveedor__nombre'])
        worksheet_margen.write(row, 1, float(proveedor['margen_promedio']) / 100, percent_format)
        worksheet_margen.write(row, 2, proveedor['total_ventas'])
        worksheet_margen.write(row, 3, float(proveedor['ingresos_totales']), number_format)
        row += 1
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_proveedores_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    return response

def exportar_reporte_fiados_excel(request, fiados_pendientes, clientes_fiados, fiados_antiguedad, productos_fiados, todos_detalles_fiados, fecha_inicio, fecha_fin):
    """Exportar reporte de fiados a Excel"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})
    
    # Formato para encabezados
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4CAF50',
        'font_color': 'white',
        'border': 1
    })
    
    # Formato para números
    number_format = workbook.add_format({'num_format': '#,##0.00'})
    
    # Formato para fechas
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # Formato para estados
    estado_pendiente_format = workbook.add_format({'bg_color': '#FFF3CD', 'border': 1})
    estado_pagado_format = workbook.add_format({'bg_color': '#D1EDBF', 'border': 1})
    estado_cancelado_format = workbook.add_format({'bg_color': '#F8D7DA', 'border': 1})
    estado_abonado_format = workbook.add_format({'bg_color': '#D1ECF1', 'border': 1})
    
    # Hoja 1: Fiados Pendientes
    worksheet1 = workbook.add_worksheet('Fiados Pendientes')
    worksheet1.write(0, 0, 'Reporte de Fiados Pendientes', header_format)
    worksheet1.write(1, 0, f'Período: {fecha_inicio} a {fecha_fin}', header_format)
    
    headers = ['Cliente', 'Fecha', 'Monto', 'Descripción', 'Días Vencido']
    for col, header in enumerate(headers):
        worksheet1.write(3, col, header, header_format)
    
    for row, fiado in enumerate(fiados_pendientes, 4):
        dias_vencido = (timezone.now().date() - fiado.fecha.date()).days
        worksheet1.write(row, 0, fiado.cliente.nombre)
        worksheet1.write(row, 1, fiado.fecha.strftime('%Y-%m-%d'))
        worksheet1.write(row, 2, float(fiado.monto), number_format)
        worksheet1.write(row, 3, f"Fiado #{fiado.id}")
        worksheet1.write(row, 4, dias_vencido)
    
    # Hoja 2: Resumen por Cliente
    worksheet2 = workbook.add_worksheet('Resumen por Cliente')
    worksheet2.write(0, 0, 'Resumen de Fiados por Cliente', header_format)
    
    headers = ['Cliente', 'Total Fiado', 'Cantidad Fiados', 'Promedio por Fiado']
    for col, header in enumerate(headers):
        worksheet2.write(2, col, header, header_format)
    
    for row, cliente in enumerate(clientes_fiados, 3):
        worksheet2.write(row, 0, cliente.nombre)
        worksheet2.write(row, 1, float(cliente.total_fiado), number_format)
        worksheet2.write(row, 2, cliente.cantidad_fiados)
        worksheet2.write(row, 3, float(cliente.promedio_fiado), number_format)
    
    # Hoja 3: Productos más fiados
    worksheet3 = workbook.add_worksheet('Productos más fiados')
    worksheet3.write(0, 0, 'Productos más fiados', header_format)
    
    headers = ['Producto', 'Categoría', 'Total Cantidad', 'Total Valor', 'Cantidad Fiados']
    for col, header in enumerate(headers):
        worksheet3.write(2, col, header, header_format)
    
    for row, producto in enumerate(productos_fiados, 3):
        worksheet3.write(row, 0, producto['producto__nombre'])
        worksheet3.write(row, 1, producto['producto__categoria__nombre'])
        worksheet3.write(row, 2, float(producto['total_cantidad']))
        worksheet3.write(row, 3, float(producto['total_valor']), number_format)
        worksheet3.write(row, 4, producto['cantidad_fiados'])
    
    # Hoja 4: TODOS los detalles de fiados (incluyendo cancelados, pagados, etc.)
    worksheet4 = workbook.add_worksheet('Todos los Detalles')
    worksheet4.set_column('A:A', 25)  # Cliente
    worksheet4.set_column('B:B', 12)  # Fecha Fiado
    worksheet4.set_column('C:C', 15)  # ID Fiado
    worksheet4.set_column('D:D', 25)  # Producto
    worksheet4.set_column('E:E', 10)  # Cantidad
    worksheet4.set_column('F:F', 12)  # Precio Unit
    worksheet4.set_column('G:G', 12)  # Subtotal
    worksheet4.set_column('H:H', 12)  # Estado
    worksheet4.set_column('I:I', 15)  # Fecha Pago
    worksheet4.set_column('J:J', 10)  # Días Vencido
    
    worksheet4.write(0, 0, 'TODOS LOS DETALLES DE FIADOS - ESTADO COMPLETO', header_format)
    worksheet4.write(1, 0, f'Período: {fecha_inicio} a {fecha_fin}', header_format)
    worksheet4.write(2, 0, f'Incluye: Pendientes, Pagados, Cancelados y Abonados', header_format)
    
    headers = ['Cliente', 'Fecha Fiado', 'ID Fiado', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal', 'Estado', 'Fecha Pago', 'Días Vencido']
    for col, header in enumerate(headers):
        worksheet4.write(4, col, header, header_format)
    
    row = 5
    for detalle in todos_detalles_fiados:
        # Determinar formato según estado
        if detalle.estado == 'pendiente':
            estado_format = estado_pendiente_format
        elif detalle.estado == 'pagado':
            estado_format = estado_pagado_format
        elif detalle.estado == 'cancelado':
            estado_format = estado_cancelado_format
        elif detalle.estado == 'abonado':
            estado_format = estado_abonado_format
        else:
            estado_format = None
        
        # Calcular días vencido
        dias_vencido = (timezone.now().date() - detalle.fiado.fecha.date()).days
        
        # Escribir datos
        worksheet4.write(row, 0, detalle.fiado.cliente.nombre)
        worksheet4.write(row, 1, detalle.fiado.fecha.strftime('%Y-%m-%d'), date_format)
        worksheet4.write(row, 2, detalle.fiado.id)
        worksheet4.write(row, 3, detalle.producto.nombre)
        worksheet4.write(row, 4, detalle.cantidad)
        worksheet4.write(row, 5, float(detalle.precio_unitario), number_format)
        worksheet4.write(row, 6, float(detalle.subtotal), number_format)
        
        # Estado con formato de color
        if estado_format:
            worksheet4.write(row, 7, detalle.estado.upper(), estado_format)
        else:
            worksheet4.write(row, 7, detalle.estado.upper())
        
        # Fecha de pago
        if detalle.fecha_pago:
            worksheet4.write(row, 8, detalle.fecha_pago.strftime('%Y-%m-%d'), date_format)
        else:
            worksheet4.write(row, 8, 'N/A')
        
        worksheet4.write(row, 9, dias_vencido)
        row += 1
    
    # Hoja 5: Resumen por Estado
    worksheet5 = workbook.add_worksheet('Resumen por Estado')
    worksheet5.write(0, 0, 'RESUMEN POR ESTADO DE PRODUCTOS', header_format)
    worksheet5.write(1, 0, f'Período: {fecha_inicio} a {fecha_fin}', header_format)
    
    # Calcular estadísticas por estado
    estados_stats = {}
    for detalle in todos_detalles_fiados:
        estado = detalle.estado
        if estado not in estados_stats:
            estados_stats[estado] = {
                'cantidad_productos': 0,
                'total_cantidad': 0,
                'total_valor': 0,
                'cantidad_fiados': set()
            }
        
        estados_stats[estado]['cantidad_productos'] += 1
        estados_stats[estado]['total_cantidad'] += detalle.cantidad
        estados_stats[estado]['total_valor'] += float(detalle.subtotal)
        estados_stats[estado]['cantidad_fiados'].add(detalle.fiado.id)
    
    headers = ['Estado', 'Cantidad Productos', 'Total Cantidad', 'Total Valor', 'Cantidad Fiados', 'Promedio por Producto']
    for col, header in enumerate(headers):
        worksheet5.write(3, col, header, header_format)
    
    row = 4
    for estado, stats in estados_stats.items():
        promedio = stats['total_valor'] / stats['cantidad_productos'] if stats['cantidad_productos'] > 0 else 0
        
        # Aplicar formato según estado
        if estado == 'pendiente':
            estado_format = estado_pendiente_format
        elif estado == 'pagado':
            estado_format = estado_pagado_format
        elif estado == 'cancelado':
            estado_format = estado_cancelado_format
        elif estado == 'abonado':
            estado_format = estado_abonado_format
        else:
            estado_format = None
        
        if estado_format:
            worksheet5.write(row, 0, estado.upper(), estado_format)
        else:
            worksheet5.write(row, 0, estado.upper())
        
        worksheet5.write(row, 1, stats['cantidad_productos'])
        worksheet5.write(row, 2, stats['total_cantidad'])
        worksheet5.write(row, 3, stats['total_valor'], number_format)
        worksheet5.write(row, 4, len(stats['cantidad_fiados']))
        worksheet5.write(row, 5, promedio, number_format)
        row += 1
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_fiados_completo_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    return response

@login_required
def reporte_categorias(request):
    """Reporte profesional de rendimiento por categorías con métricas avanzadas"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    categoria_id = request.GET.get('categoria_id')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Obtener todas las categorías para el filtro
    todas_categorias = Categoria.objects.filter(activo=True).order_by('nombre')
    
    # Filtro base para productos
    productos_filter = Producto.objects.filter(
        categoria__isnull=False,
        detalleventa__venta__fecha__range=(fecha_inicio, fecha_fin)
    )
    
    # Aplicar filtro de categoría si se especifica
    if categoria_id and categoria_id != 'None':
        productos_filter = productos_filter.filter(categoria_id=categoria_id)
    
    # Análisis principal por categorías con métricas mejoradas
    categorias_analisis = productos_filter.values(
        'categoria__nombre',
        'categoria__id',
        'categoria__descripcion'
    ).annotate(
        total_productos=Count('id', distinct=True),
        total_vendido=Sum('detalleventa__cantidad'),
        total_ingresos=Sum(F('detalleventa__cantidad') * F('detalleventa__precio_unitario')),
        costo_total=Sum(F('detalleventa__cantidad') * F('precio')),
        margen_ganancia=ExpressionWrapper(
            Sum(F('detalleventa__cantidad') * F('detalleventa__precio_unitario')) - 
            Sum(F('detalleventa__cantidad') * F('precio')),
            output_field=DecimalField()
        ),
        promedio_precio=Avg('precio'),
        stock_total=Sum('stock_actual'),
        valor_inventario=Sum(F('stock_actual') * F('precio')),
        productos_bajo_stock=Count('id', filter=Q(stock_actual__lte=F('stock_minimo'))),
        productos_sin_stock=Count('id', filter=Q(stock_actual=0)),
        rotacion_inventario=ExpressionWrapper(
            Sum('detalleventa__cantidad') * 365.0 / (Sum('stock_actual') + 1),
            output_field=DecimalField()
        )
    ).order_by('-total_ingresos')
    
    # Calcular métricas adicionales
    for categoria in categorias_analisis:
        if categoria['total_ingresos'] and categoria['total_ingresos'] > 0:
            categoria['porcentaje_margen'] = (categoria['margen_ganancia'] / categoria['total_ingresos']) * 100
        else:
            categoria['porcentaje_margen'] = 0
        
        # Calcular eficiencia de inventario
        if categoria['stock_total'] > 0:
            categoria['eficiencia_inventario'] = (categoria['total_vendido'] / categoria['stock_total']) * 100
        else:
            categoria['eficiencia_inventario'] = 0
        
        # Calcular días de inventario
        if categoria['total_vendido'] > 0:
            categoria['dias_inventario'] = (categoria['stock_total'] / categoria['total_vendido']) * 30
        else:
            categoria['dias_inventario'] = 999
    
    # Productos más vendidos por categoría (top 5 por categoría)
    productos_por_categoria = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin),
        producto__categoria__isnull=False
    )
    
    if categoria_id and categoria_id != 'None':
        productos_por_categoria = productos_por_categoria.filter(producto__categoria_id=categoria_id)
    
    productos_por_categoria = productos_por_categoria.values(
        'producto__categoria__nombre',
        'producto__nombre',
        'producto__categoria__id'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario')),
        promedio_precio=Avg('precio_unitario')
    ).order_by('producto__categoria__nombre', '-total_vendido')
    
    # Categorías con mejor rendimiento por margen
    categorias_rendimiento = sorted(
        categorias_analisis, 
        key=lambda x: x['porcentaje_margen'], 
        reverse=True
    )
    
    # Categorías con mejor rotación de inventario
    categorias_rotacion = sorted(
        categorias_analisis,
        key=lambda x: x['rotacion_inventario'],
        reverse=True
    )
    
    # Análisis de tendencias por mes
    tendencias_mensuales = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin),
        producto__categoria__isnull=False
    ).values(
        'producto__categoria__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('producto__categoria__nombre')
    
    # Estadísticas generales
    total_ingresos_general = sum(cat['total_ingresos'] for cat in categorias_analisis)
    total_productos_general = sum(cat['total_productos'] for cat in categorias_analisis)
    total_stock_general = sum(cat['stock_total'] for cat in categorias_analisis)
    
    # Calcular porcentajes de participación
    for categoria in categorias_analisis:
        if total_ingresos_general > 0:
            categoria['porcentaje_participacion'] = (categoria['total_ingresos'] / total_ingresos_general) * 100
        else:
            categoria['porcentaje_participacion'] = 0
    
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_categorias_excel(
            request,
            categorias_analisis,
            productos_por_categoria,
            categorias_rendimiento,
            categorias_rotacion,
            tendencias_mensuales,
            fecha_inicio,
            fecha_fin
        )
    
    context = {
        'categorias_analisis': categorias_analisis,
        'productos_por_categoria': productos_por_categoria,
        'categorias_rendimiento': categorias_rendimiento,
        'categorias_rotacion': categorias_rotacion,
        'tendencias_mensuales': tendencias_mensuales,
        'todas_categorias': todas_categorias,
        'categoria_seleccionada': categoria_id,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'total_ingresos_general': total_ingresos_general,
        'total_productos_general': total_productos_general,
        'total_stock_general': total_stock_general,
    }
    return render(request, 'reportes/reporte_categorias.html', context)

def exportar_reporte_categorias_excel(request, categorias_analisis, productos_por_categoria, categorias_rendimiento, categorias_rotacion, tendencias_mensuales, fecha_inicio, fecha_fin):
    """Exportar reporte de categorías a Excel"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})
    
    # Formato para encabezados
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#2196F3',
        'font_color': 'white',
        'border': 1
    })
    
    # Hoja 1: Análisis por Categorías
    worksheet1 = workbook.add_worksheet('Analisis Categorias')
    worksheet1.write(0, 0, 'Reporte de Rendimiento por Categorías', header_format)
    worksheet1.write(1, 0, f'Período: {fecha_inicio.strftime("%Y-%m-%d")} a {fecha_fin.strftime("%Y-%m-%d")}', header_format)
    
    headers = ['Categoría', 'Productos', 'Total Vendido', 'Ingresos', 'Costo Total', 'Margen', '% Margen', 'Stock Total', 'Valor Inventario', 'Productos Bajo Stock', 'Productos Sin Stock', 'Rotación Inventario']
    for col, header in enumerate(headers):
        worksheet1.write(3, col, header, header_format)
    
    for row, categoria in enumerate(categorias_analisis, 4):
        worksheet1.write(row, 0, categoria['categoria__nombre'])
        worksheet1.write(row, 1, categoria['total_productos'])
        worksheet1.write(row, 2, categoria['total_vendido'])
        worksheet1.write(row, 3, float(categoria['total_ingresos']))
        worksheet1.write(row, 4, float(categoria['costo_total']))
        worksheet1.write(row, 5, float(categoria['margen_ganancia']))
        worksheet1.write(row, 6, round(categoria['porcentaje_margen'], 2))
        worksheet1.write(row, 7, categoria['stock_total'])
        worksheet1.write(row, 8, float(categoria['valor_inventario']))
        worksheet1.write(row, 9, categoria['productos_bajo_stock'])
        worksheet1.write(row, 10, categoria['productos_sin_stock'])
        worksheet1.write(row, 11, float(categoria['rotacion_inventario']))
    
    # Hoja 2: Productos por Categoría
    worksheet2 = workbook.add_worksheet('Productos por Categoria')
    worksheet2.write(0, 0, 'Productos Más Vendidos por Categoría', header_format)
    
    headers = ['Categoría', 'Producto', 'Total Vendido', 'Ingresos', 'Promedio Precio']
    for col, header in enumerate(headers):
        worksheet2.write(2, col, header, header_format)
    
    for row, producto in enumerate(productos_por_categoria, 3):
        worksheet2.write(row, 0, producto['producto__categoria__nombre'])
        worksheet2.write(row, 1, producto['producto__nombre'])
        worksheet2.write(row, 2, producto['total_vendido'])
        worksheet2.write(row, 3, float(producto['total_ingresos']))
        worksheet2.write(row, 4, float(producto['promedio_precio']))
    
    # Hoja 3: Categorías con Mejor Rendimiento
    worksheet3 = workbook.add_worksheet('Mejor Rendimiento')
    worksheet3.write(0, 0, 'Categorías con Mejor Rendimiento', header_format)
    
    headers = ['Categoría', 'Porcentaje Margen', 'Porcentaje Participación', 'Total Productos', 'Total Vendido', 'Total Ingresos', 'Costo Total', 'Margen', 'Promedio Precio', 'Stock Total', 'Valor Inventario', 'Productos Bajo Stock', 'Productos Sin Stock', 'Rotación Inventario']
    for col, header in enumerate(headers):
        worksheet3.write(2, col, header, header_format)
    
    for row, categoria in enumerate(categorias_rendimiento, 3):
        worksheet3.write(row, 0, categoria['categoria__nombre'])
        worksheet3.write(row, 1, round(categoria['porcentaje_margen'], 2))
        worksheet3.write(row, 2, round(categoria['porcentaje_participacion'], 2))
        worksheet3.write(row, 3, categoria['total_productos'])
        worksheet3.write(row, 4, categoria['total_vendido'])
        worksheet3.write(row, 5, float(categoria['total_ingresos']))
        worksheet3.write(row, 6, float(categoria['costo_total']))
        worksheet3.write(row, 7, float(categoria['margen_ganancia']))
        worksheet3.write(row, 8, float(categoria['promedio_precio']))
        worksheet3.write(row, 9, categoria['stock_total'])
        worksheet3.write(row, 10, float(categoria['valor_inventario']))
        worksheet3.write(row, 11, categoria['productos_bajo_stock'])
        worksheet3.write(row, 12, categoria['productos_sin_stock'])
        worksheet3.write(row, 13, float(categoria['rotacion_inventario']))
    
    # Hoja 4: Categorías con Mejor Rotación
    worksheet4 = workbook.add_worksheet('Mejor Rotacion')
    worksheet4.write(0, 0, 'Categorías con Mejor Rotación', header_format)
    
    headers = ['Categoría', 'Porcentaje Margen', 'Porcentaje Participación', 'Total Productos', 'Total Vendido', 'Total Ingresos', 'Costo Total', 'Margen', 'Promedio Precio', 'Stock Total', 'Valor Inventario', 'Productos Bajo Stock', 'Productos Sin Stock', 'Rotación Inventario']
    for col, header in enumerate(headers):
        worksheet4.write(2, col, header, header_format)
    
    for row, categoria in enumerate(categorias_rotacion, 3):
        worksheet4.write(row, 0, categoria['categoria__nombre'])
        worksheet4.write(row, 1, round(categoria['porcentaje_margen'], 2))
        worksheet4.write(row, 2, round(categoria['porcentaje_participacion'], 2))
        worksheet4.write(row, 3, categoria['total_productos'])
        worksheet4.write(row, 4, categoria['total_vendido'])
        worksheet4.write(row, 5, float(categoria['total_ingresos']))
        worksheet4.write(row, 6, float(categoria['costo_total']))
        worksheet4.write(row, 7, float(categoria['margen_ganancia']))
        worksheet4.write(row, 8, float(categoria['promedio_precio']))
        worksheet4.write(row, 9, categoria['stock_total'])
        worksheet4.write(row, 10, float(categoria['valor_inventario']))
        worksheet4.write(row, 11, categoria['productos_bajo_stock'])
        worksheet4.write(row, 12, categoria['productos_sin_stock'])
        worksheet4.write(row, 13, float(categoria['rotacion_inventario']))
    
    # Hoja 5: Análisis de Tendencias Mensuales
    worksheet5 = workbook.add_worksheet('Tendencias Mensuales')
    worksheet5.write(0, 0, 'Análisis de Tendencias Mensuales', header_format)
    
    headers = ['Categoría', 'Mes', 'Año', 'Total Vendido', 'Total Ingresos', 'Promedio Precio']
    for col, header in enumerate(headers):
        worksheet5.write(2, col, header, header_format)
    
    for row, tendencia in enumerate(tendencias_mensuales, 3):
        worksheet5.write(row, 0, tendencia['producto__categoria__nombre'])
        worksheet5.write(row, 1, tendencia['mes'])
        worksheet5.write(row, 2, tendencia['año'])
        worksheet5.write(row, 3, tendencia['total_vendido'])
        worksheet5.write(row, 4, float(tendencia['total_ingresos']))
        worksheet5.write(row, 5, float(tendencia['total_ingresos'] / tendencia['total_vendido']))
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_categorias_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    return response

def exportar_reporte_productos_excel(request, productos_bajo_stock, productos_mas_vendidos, productos_rotacion, fecha_inicio, fecha_fin):
    """Exportar reporte de productos a Excel con formato profesional y mejor organización"""
    
    # Crear el archivo Excel en memoria
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Definir formatos mejorados
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'vcenter',
        'align': 'center',
        'fg_color': '#2E75B6',
        'font_color': 'white',
        'border': 1,
        'font_size': 11
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 18,
        'align': 'center',
        'fg_color': '#1F4E79',
        'font_color': 'white',
        'border': 1,
        'valign': 'vcenter'
    })
    
    subtitle_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'fg_color': '#4472C4',
        'font_color': 'white',
        'border': 1,
        'align': 'center'
    })
    
    date_format = workbook.add_format({
        'num_format': 'dd/mm/yyyy',
        'border': 1,
        'align': 'center'
    })
    
    currency_format = workbook.add_format({
        'num_format': '$#,##0.00',
        'border': 1,
        'align': 'right'
    })
    
    number_format = workbook.add_format({
        'num_format': '#,##0',
        'border': 1,
        'align': 'center'
    })
    
    percent_format = workbook.add_format({
        'num_format': '0.00%',
        'border': 1,
        'align': 'center'
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    warning_format = workbook.add_format({
        'fg_color': '#FFE6CC',
        'border': 1,
        'font_color': '#CC6600',
        'bold': True,
        'align': 'center'
    })
    
    critical_format = workbook.add_format({
        'fg_color': '#FFCCCC',
        'border': 1,
        'font_color': '#CC0000',
        'bold': True,
        'align': 'center'
    })
    
    info_format = workbook.add_format({
        'fg_color': '#E6F3FF',
        'border': 1,
        'font_color': '#0066CC',
        'align': 'left'
    })
    
    # ===== HOJA 1: RESUMEN EJECUTIVO =====
    summary_sheet = workbook.add_worksheet('📊 RESUMEN EJECUTIVO')
    
    # Título principal
    summary_sheet.merge_range('A1:J1', 'REPORTE DE PRODUCTOS - TRADE INVENTORY', title_format)
    summary_sheet.merge_range('A2:J2', f'Período de Análisis: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}', subtitle_format)
    
    # Información del reporte
    summary_sheet.write('A4', '📅 Fecha de Generación:', info_format)
    summary_sheet.write('B4', timezone.now().strftime("%d/%m/%Y %H:%M"), date_format)
    
    summary_sheet.write('A5', '👤 Generado por:', info_format)
    summary_sheet.write('B5', request.user.get_full_name() or request.user.username, cell_format)
    
    # Estadísticas generales
    total_productos = Producto.objects.count()
    productos_bajo_stock_count = productos_bajo_stock.count()
    productos_sin_stock = Producto.objects.filter(stock_actual=0).count()
    valor_total_inventario = sum(p.stock_actual * p.precio for p in Producto.objects.all())
    productos_con_ventas = len(productos_mas_vendidos)
    
    # Sección de estadísticas
    summary_sheet.write('A7', '📈 ESTADÍSTICAS GENERALES DEL INVENTARIO', subtitle_format)
    
    # Primera columna
    summary_sheet.write('A8', 'Total de Productos:', header_format)
    summary_sheet.write('B8', total_productos, number_format)
    
    summary_sheet.write('A9', 'Productos Bajo Stock:', header_format)
    summary_sheet.write('B9', productos_bajo_stock_count, number_format)
    
    summary_sheet.write('A10', 'Productos Sin Stock:', header_format)
    summary_sheet.write('B10', productos_sin_stock, number_format)
    
    summary_sheet.write('A11', 'Productos con Ventas:', header_format)
    summary_sheet.write('B11', productos_con_ventas, number_format)
    
    # Segunda columna
    summary_sheet.write('D8', 'Valor Total Inventario:', header_format)
    summary_sheet.write('E8', valor_total_inventario, currency_format)
    
    summary_sheet.write('D9', '% Productos Bajo Stock:', header_format)
    summary_sheet.write('E9', productos_bajo_stock_count / total_productos if total_productos > 0 else 0, percent_format)
    
    summary_sheet.write('D10', '% Productos Sin Stock:', header_format)
    summary_sheet.write('E10', productos_sin_stock / total_productos if total_productos > 0 else 0, percent_format)
    
    summary_sheet.write('D11', '% Productos Activos:', header_format)
    summary_sheet.write('E11', productos_con_ventas / total_productos if total_productos > 0 else 0, percent_format)
    
    # Alertas y recomendaciones
    summary_sheet.write('A13', '⚠️ ALERTAS Y RECOMENDACIONES', subtitle_format)
    
    row = 14
    if productos_sin_stock > 0:
        summary_sheet.write(f'A{row}', f'🚨 CRÍTICO: {productos_sin_stock} productos sin stock', critical_format)
        summary_sheet.merge_range(f'B{row}:J{row}', 'Reabastecimiento urgente requerido', info_format)
        row += 1
    
    if productos_bajo_stock_count > 0:
        summary_sheet.write(f'A{row}', f'⚠️ ATENCIÓN: {productos_bajo_stock_count} productos bajo stock', warning_format)
        summary_sheet.merge_range(f'B{row}:J{row}', 'Revisar niveles de inventario y reabastecer', info_format)
        row += 1
    
    if productos_con_ventas < total_productos * 0.5:
        summary_sheet.write(f'A{row}', f'📊 BAJA ROTACIÓN: Solo {productos_con_ventas} de {total_productos} productos tienen ventas', warning_format)
        summary_sheet.merge_range(f'B{row}:J{row}', 'Considerar promociones o descuentos para productos sin movimiento', info_format)
    
    # ===== HOJA 2: PRODUCTOS BAJO STOCK =====
    stock_sheet = workbook.add_worksheet('⚠️ BAJO STOCK')
    
    # Título
    stock_sheet.merge_range('A1:H1', 'PRODUCTOS BAJO STOCK - ACCIÓN REQUERIDA', title_format)
    
    # Encabezados
    headers = ['ID', 'Producto', 'Categoría', 'Proveedor', 'Stock Actual', 'Stock Mínimo', 'Déficit', 'Prioridad']
    for col, header in enumerate(headers):
        stock_sheet.write(2, col, header, header_format)
    
    # Datos
    row = 3
    for producto in productos_bajo_stock:
        stock_sheet.write(row, 0, producto.id, number_format)
        stock_sheet.write(row, 1, producto.nombre, cell_format)
        stock_sheet.write(row, 2, producto.categoria.nombre if producto.categoria else 'Sin categoría', cell_format)
        stock_sheet.write(row, 3, producto.proveedor.nombre if producto.proveedor else 'Sin proveedor', cell_format)
        stock_sheet.write(row, 4, producto.stock_actual, number_format)
        stock_sheet.write(row, 5, producto.stock_minimo, number_format)
        
        # Calcular déficit
        deficit = producto.stock_minimo - producto.stock_actual
        stock_sheet.write(row, 6, deficit, number_format)
        
        # Prioridad
        if producto.stock_actual == 0:
            prioridad = 'URGENTE'
            format_prioridad = critical_format
        elif producto.stock_actual <= producto.stock_minimo * 0.5:
            prioridad = 'ALTA'
            format_prioridad = warning_format
        else:
            prioridad = 'MEDIA'
            format_prioridad = cell_format
        
        stock_sheet.write(row, 7, prioridad, format_prioridad)
        row += 1
    
    # Ajustar ancho de columnas
    stock_sheet.set_column('A:A', 8)   # ID
    stock_sheet.set_column('B:B', 35)  # Producto
    stock_sheet.set_column('C:C', 20)  # Categoría
    stock_sheet.set_column('D:D', 25)  # Proveedor
    stock_sheet.set_column('E:G', 12)  # Stock y Déficit
    stock_sheet.set_column('H:H', 15)  # Prioridad
    
    # ===== HOJA 3: PRODUCTOS MÁS VENDIDOS =====
    ventas_sheet = workbook.add_worksheet('🏆 TOP VENTAS')
    
    # Título
    ventas_sheet.merge_range('A1:G1', 'PRODUCTOS MÁS VENDIDOS - ANÁLISIS DE RENDIMIENTO', title_format)
    
    # Encabezados
    headers = ['Ranking', 'Producto', 'Categoría', 'Proveedor', 'Unidades Vendidas', 'Ingresos Totales', 'Precio Promedio']
    for col, header in enumerate(headers):
        ventas_sheet.write(2, col, header, header_format)
    
    # Datos
    row = 3
    for i, producto in enumerate(productos_mas_vendidos, 1):
        ventas_sheet.write(row, 0, i, number_format)  # Ranking
        ventas_sheet.write(row, 1, producto['producto__nombre'], cell_format)
        ventas_sheet.write(row, 2, producto['producto__categoria__nombre'] or 'Sin categoría', cell_format)
        ventas_sheet.write(row, 3, producto['producto__proveedor__nombre'] or 'Sin proveedor', cell_format)
        ventas_sheet.write(row, 4, producto['total_vendido'], number_format)
        ventas_sheet.write(row, 5, producto['total_ingresos'], currency_format)
        
        # Precio promedio por unidad
        promedio = producto['total_ingresos'] / producto['total_vendido'] if producto['total_vendido'] > 0 else 0
        ventas_sheet.write(row, 6, promedio, currency_format)
        row += 1
    
    # Ajustar ancho de columnas
    ventas_sheet.set_column('A:A', 10)  # Ranking
    ventas_sheet.set_column('B:B', 35)  # Producto
    ventas_sheet.set_column('C:C', 20)  # Categoría
    ventas_sheet.set_column('D:D', 25)  # Proveedor
    ventas_sheet.set_column('E:E', 15)  # Unidades
    ventas_sheet.set_column('F:G', 18)  # Montos
    
    # ===== HOJA 4: ROTACIÓN DE INVENTARIO =====
    rotacion_sheet = workbook.add_worksheet('🔄 ROTACIÓN')
    
    # Título
    rotacion_sheet.merge_range('A1:G1', 'ROTACIÓN DE INVENTARIO - ANÁLISIS DE MOVIMIENTO', title_format)
    
    # Encabezados
    headers = ['Producto', 'Categoría', 'Stock Actual', 'Unidades Vendidas', 'Valor Vendido', 'Índice Rotación', 'Estado']
    for col, header in enumerate(headers):
        rotacion_sheet.write(2, col, header, header_format)
    
    # Datos
    row = 3
    for producto in productos_rotacion:
        rotacion_sheet.write(row, 0, producto['nombre'], cell_format)
        rotacion_sheet.write(row, 1, producto['categoria__nombre'] or 'Sin categoría', cell_format)
        rotacion_sheet.write(row, 2, producto['stock_actual'], number_format)
        rotacion_sheet.write(row, 3, producto['unidades_vendidas'], number_format)
        rotacion_sheet.write(row, 4, producto['valor_vendido'], currency_format)
        
        # Índice de rotación
        indice_rotacion = producto['unidades_vendidas'] / producto['stock_actual'] if producto['stock_actual'] > 0 else 0
        rotacion_sheet.write(row, 5, indice_rotacion, number_format)
        
        # Estado de rotación
        if indice_rotacion >= 2:
            estado = 'ALTA'
            format_estado = cell_format
        elif indice_rotacion >= 1:
            estado = 'MEDIA'
            format_estado = cell_format
        else:
            estado = 'BAJA'
            format_estado = warning_format
        
        rotacion_sheet.write(row, 6, estado, format_estado)
        row += 1
    
    # Ajustar ancho de columnas
    rotacion_sheet.set_column('A:A', 35)  # Producto
    rotacion_sheet.set_column('B:B', 20)  # Categoría
    rotacion_sheet.set_column('C:D', 15)  # Stock y Unidades
    rotacion_sheet.set_column('E:E', 18)  # Valor
    rotacion_sheet.set_column('F:F', 18)  # Índice
    rotacion_sheet.set_column('G:G', 12)  # Estado
    
    # ===== HOJA 5: INVENTARIO COMPLETO =====
    inventario_sheet = workbook.add_worksheet('📋 INVENTARIO COMPLETO')
    
    # Título
    inventario_sheet.merge_range('A1:J1', 'INVENTARIO COMPLETO - VISTA GENERAL', title_format)
    
    # Encabezados
    headers = ['ID', 'Producto', 'Categoría', 'Proveedor', 'Stock Actual', 'Stock Mínimo', 'Precio Unit.', 'Valor Total', 'Estado', 'Última Venta']
    for col, header in enumerate(headers):
        inventario_sheet.write(2, col, header, header_format)
    
    # Obtener todos los productos con información de última venta
    todos_productos = Producto.objects.select_related('categoria', 'proveedor').order_by('nombre')
    
    # Datos
    row = 3
    for producto in todos_productos:
        inventario_sheet.write(row, 0, producto.id, number_format)
        inventario_sheet.write(row, 1, producto.nombre, cell_format)
        inventario_sheet.write(row, 2, producto.categoria.nombre if producto.categoria else 'Sin categoría', cell_format)
        inventario_sheet.write(row, 3, producto.proveedor.nombre if producto.proveedor else 'Sin proveedor', cell_format)
        inventario_sheet.write(row, 4, producto.stock_actual, number_format)
        inventario_sheet.write(row, 5, producto.stock_minimo, number_format)
        inventario_sheet.write(row, 6, producto.precio, currency_format)
        
        # Valor total
        valor_total = producto.stock_actual * producto.precio
        inventario_sheet.write(row, 7, valor_total, currency_format)
        
        # Estado del stock
        if producto.stock_actual == 0:
            estado = 'SIN STOCK'
            format_estado = critical_format
        elif producto.stock_actual <= producto.stock_minimo:
            estado = 'BAJO'
            format_estado = warning_format
        else:
            estado = 'NORMAL'
            format_estado = cell_format
        
        inventario_sheet.write(row, 8, estado, format_estado)
        
        # Última venta (simplificado)
        inventario_sheet.write(row, 9, 'N/A', cell_format)
        row += 1
    
    # Ajustar ancho de columnas
    inventario_sheet.set_column('A:A', 8)   # ID
    inventario_sheet.set_column('B:B', 35)  # Producto
    inventario_sheet.set_column('C:C', 20)  # Categoría
    inventario_sheet.set_column('D:D', 25)  # Proveedor
    inventario_sheet.set_column('E:F', 12)  # Stock
    inventario_sheet.set_column('G:H', 15)  # Precios
    inventario_sheet.set_column('I:I', 12)  # Estado
    inventario_sheet.set_column('J:J', 15)  # Última Venta
    
    # ===== HOJA 6: GRÁFICOS Y ANÁLISIS =====
    if productos_mas_vendidos:
        chart_sheet = workbook.add_worksheet('📊 GRÁFICOS')
        
        # Título
        chart_sheet.merge_range('A1:H1', 'GRÁFICOS Y ANÁLISIS VISUAL', title_format)
        
        # Gráfico de productos más vendidos
        chart = workbook.add_chart({'type': 'column'})
        chart.set_title({'name': 'Top 10 Productos Más Vendidos'})
        chart.set_x_axis({'name': 'Productos'})
        chart.set_y_axis({'name': 'Unidades Vendidas'})
        chart.set_size({'width': 720, 'height': 400})
        
        # Agregar datos al gráfico
        chart.add_series({
            'name': 'Unidades Vendidas',
            'categories': f'=🏆 TOP VENTAS!$B$3:$B${2 + len(productos_mas_vendidos)}',
            'values': f'=🏆 TOP VENTAS!$E$3:$E${2 + len(productos_mas_vendidos)}',
            'fill': {'color': '#4472C4'}
        })
        
        chart_sheet.insert_chart('A3', chart)
        
        # Gráfico de ingresos
        chart2 = workbook.add_chart({'type': 'bar'})
        chart2.set_title({'name': 'Top 10 Productos por Ingresos'})
        chart2.set_x_axis({'name': 'Ingresos ($)'})
        chart2.set_y_axis({'name': 'Productos'})
        chart2.set_size({'width': 720, 'height': 400})
        
        chart2.add_series({
            'name': 'Ingresos Totales',
            'categories': f'=🏆 TOP VENTAS!$B$3:$B${2 + len(productos_mas_vendidos)}',
            'values': f'=🏆 TOP VENTAS!$F$3:$F${2 + len(productos_mas_vendidos)}',
            'fill': {'color': '#70AD47'}
        })
        
        chart_sheet.insert_chart('A25', chart2)
    
    # Cerrar el workbook
    workbook.close()
    
    # Preparar la respuesta HTTP
    output.seek(0)
    filename = f'Reporte_Productos_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def exportar_reporte_ventas_excel(request, ventas_por_dia, ventas_por_mes, productos_top, fecha_inicio, fecha_fin):
    """Exportar reporte de ventas a Excel con formato profesional y mejor organización"""
    
    # Crear el archivo Excel en memoria
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Definir formatos mejorados
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'vcenter',
        'align': 'center',
        'fg_color': '#2E75B6',
        'font_color': 'white',
        'border': 1,
        'font_size': 11
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 18,
        'align': 'center',
        'fg_color': '#1F4E79',
        'font_color': 'white',
        'border': 1,
        'valign': 'vcenter'
    })
    
    subtitle_format = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'fg_color': '#4472C4',
        'font_color': 'white',
        'border': 1,
        'align': 'center'
    })
    
    date_format = workbook.add_format({
        'num_format': 'dd/mm/yyyy',
        'border': 1,
        'align': 'center'
    })
    
    currency_format = workbook.add_format({
        'num_format': '$#,##0.00',
        'border': 1,
        'align': 'right'
    })
    
    number_format = workbook.add_format({
        'num_format': '#,##0',
        'border': 1,
        'align': 'center'
    })
    
    percent_format = workbook.add_format({
        'num_format': '0.00%',
        'border': 1,
        'align': 'center'
    })
    
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
        'text_wrap': True
    })
    
    positive_format = workbook.add_format({
        'fg_color': '#E6F3FF',
        'border': 1,
        'font_color': '#0066CC',
        'align': 'right',
        'num_format': '$#,##0.00'
    })
    
    negative_format = workbook.add_format({
        'fg_color': '#FFE6E6',
        'border': 1,
        'font_color': '#CC0000',
        'align': 'right',
        'num_format': '$#,##0.00'
    })
    
    info_format = workbook.add_format({
        'fg_color': '#E6F3FF',
        'border': 1,
        'font_color': '#0066CC',
        'align': 'left'
    })
    
    # Función auxiliar para convertir fechas con timezone a datetime sin timezone
    def convert_to_naive_datetime(dt):
        """Convierte datetime con timezone a datetime sin timezone"""
        if dt and hasattr(dt, 'replace'):
            return dt.replace(tzinfo=None)
        return dt
    
    # ===== HOJA 1: RESUMEN EJECUTIVO =====
    summary_sheet = workbook.add_worksheet('📊 RESUMEN EJECUTIVO')
    
    # Título principal
    summary_sheet.merge_range('A1:J1', 'REPORTE DE VENTAS - TRADE INVENTORY', title_format)
    summary_sheet.merge_range('A2:J2', f'Período de Análisis: {fecha_inicio.strftime("%d/%m/%Y")} - {fecha_fin.strftime("%d/%m/%Y")}', subtitle_format)
    
    # Información del reporte
    summary_sheet.write('A4', '📅 Fecha de Generación:', info_format)
    summary_sheet.write('B4', convert_to_naive_datetime(timezone.now()).strftime("%d/%m/%Y %H:%M"), date_format)
    
    summary_sheet.write('A5', '👤 Generado por:', info_format)
    summary_sheet.write('B5', request.user.get_full_name() or request.user.username, cell_format)
    
    # Estadísticas generales
    total_ventas = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin)).count()
    monto_total_ventas = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin)).aggregate(total=Sum('total'))['total'] or 0
    promedio_venta = monto_total_ventas / total_ventas if total_ventas > 0 else 0
    ventas_fiado = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin), es_fiado=True).count()
    ventas_contado = total_ventas - ventas_fiado
    
    # Calcular días con ventas
    dias_con_ventas = len(set(v['fecha'].date() for v in ventas_por_dia))
    dias_periodo = (fecha_fin - fecha_inicio).days + 1
    
    # Sección de estadísticas
    summary_sheet.write('A7', '📈 ESTADÍSTICAS GENERALES DE VENTAS', subtitle_format)
    
    # Primera columna
    summary_sheet.write('A8', 'Total de Ventas:', header_format)
    summary_sheet.write('B8', total_ventas, number_format)
    
    summary_sheet.write('A9', 'Monto Total Ventas:', header_format)
    summary_sheet.write('B9', monto_total_ventas, currency_format)
    
    summary_sheet.write('A10', 'Promedio por Venta:', header_format)
    summary_sheet.write('B10', promedio_venta, currency_format)
    
    summary_sheet.write('A11', 'Ventas al Contado:', header_format)
    summary_sheet.write('B11', ventas_contado, number_format)
    
    # Segunda columna
    summary_sheet.write('D8', 'Ventas a Fiado:', header_format)
    summary_sheet.write('E8', ventas_fiado, number_format)
    
    summary_sheet.write('D9', 'Días con Ventas:', header_format)
    summary_sheet.write('E9', dias_con_ventas, number_format)
    
    summary_sheet.write('D10', 'Promedio Diario:', header_format)
    summary_sheet.write('E10', monto_total_ventas / dias_con_ventas if dias_con_ventas > 0 else 0, currency_format)
    
    summary_sheet.write('D11', 'Eficiencia de Días:', header_format)
    summary_sheet.write('E11', dias_con_ventas / dias_periodo if dias_periodo > 0 else 0, percent_format)
    
    # Porcentajes
    summary_sheet.write('G8', '% Ventas Contado:', header_format)
    summary_sheet.write('H8', ventas_contado / total_ventas if total_ventas > 0 else 0, percent_format)
    
    summary_sheet.write('G9', '% Ventas Fiado:', header_format)
    summary_sheet.write('H9', ventas_fiado / total_ventas if total_ventas > 0 else 0, percent_format)
    
    # Análisis de tendencias
    if len(ventas_por_dia) > 1:
        # Calcular tendencia
        ventas_list = list(ventas_por_dia)
        primera_semana = sum(v['monto_total'] for v in ventas_list[:7]) if len(ventas_list) >= 7 else sum(v['monto_total'] for v in ventas_list)
        ultima_semana = sum(v['monto_total'] for v in ventas_list[-7:]) if len(ventas_list) >= 7 else sum(v['monto_total'] for v in ventas_list)
        
        tendencia = ((ultima_semana - primera_semana) / primera_semana * 100) if primera_semana > 0 else 0
        
        summary_sheet.write('A13', '📊 ANÁLISIS DE TENDENCIAS', subtitle_format)
        summary_sheet.write('A14', 'Tendencia de Ventas:', header_format)
        summary_sheet.write('B14', tendencia, percent_format)
        
        if tendencia > 0:
            summary_sheet.write('C14', '📈 CRECIMIENTO', positive_format)
        elif tendencia < 0:
            summary_sheet.write('C14', '📉 DECRECIMIENTO', negative_format)
        else:
            summary_sheet.write('C14', '➡️ ESTABLE', cell_format)
    
    # ===== HOJA 2: VENTAS POR DÍA =====
    daily_sheet = workbook.add_worksheet('📅 VENTAS DIARIAS')
    
    # Título
    daily_sheet.merge_range('A1:F1', 'VENTAS POR DÍA - ANÁLISIS DETALLADO', title_format)
    
    # Encabezados
    headers = ['Fecha', 'Total Ventas', 'Monto Total', 'Promedio por Venta', 'Ventas Contado', 'Ventas Fiado']
    for col, header in enumerate(headers):
        daily_sheet.write(2, col, header, header_format)
    
    # Datos
    row = 3
    for venta_dia in ventas_por_dia:
        # Convertir fecha a datetime sin timezone
        fecha_naive = convert_to_naive_datetime(venta_dia['fecha'])
        daily_sheet.write(row, 0, fecha_naive, date_format)
        daily_sheet.write(row, 1, venta_dia['total_ventas'], number_format)
        daily_sheet.write(row, 2, venta_dia['monto_total'], currency_format)
        daily_sheet.write(row, 3, venta_dia['promedio_venta'], currency_format)
        
        # Obtener ventas contado y fiado para este día
        ventas_contado_dia = Venta.objects.filter(
            fecha__date=venta_dia['fecha'].date(),
            es_fiado=False
        ).count()
        ventas_fiado_dia = Venta.objects.filter(
            fecha__date=venta_dia['fecha'].date(),
            es_fiado=True
        ).count()
        
        daily_sheet.write(row, 4, ventas_contado_dia, number_format)
        daily_sheet.write(row, 5, ventas_fiado_dia, number_format)
        row += 1
    
    # Ajustar ancho de columnas
    daily_sheet.set_column('A:A', 15)  # Fecha
    daily_sheet.set_column('B:B', 12)  # Total Ventas
    daily_sheet.set_column('C:D', 18)  # Montos
    daily_sheet.set_column('E:F', 15)  # Tipos de venta
    
    # ===== HOJA 3: VENTAS POR MES =====
    monthly_sheet = workbook.add_worksheet('📆 VENTAS MENSUALES')
    
    # Título
    monthly_sheet.merge_range('A1:F1', 'VENTAS POR MES - ANÁLISIS MENSUAL', title_format)
    
    # Encabezados
    headers = ['Mes/Año', 'Total Ventas', 'Monto Total', 'Promedio por Venta', 'Días con Ventas', 'Promedio Diario']
    for col, header in enumerate(headers):
        monthly_sheet.write(2, col, header, header_format)
    
    # Datos
    row = 3
    for venta_mes in ventas_por_mes:
        # Formatear mes/año
        mes_nombre = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        mes_texto = f"{mes_nombre.get(venta_mes['mes'], 'Desconocido')} {venta_mes['año']}"
        
        monthly_sheet.write(row, 0, mes_texto, cell_format)
        monthly_sheet.write(row, 1, venta_mes['total_ventas'], number_format)
        monthly_sheet.write(row, 2, venta_mes['monto_total'], currency_format)
        monthly_sheet.write(row, 3, venta_mes['promedio_venta'], currency_format)
        
        # Calcular días con ventas para este mes
        dias_mes = Venta.objects.filter(
            fecha__year=venta_mes['año'],
            fecha__month=venta_mes['mes']
        ).values('fecha__date').distinct().count()
        
        monthly_sheet.write(row, 4, dias_mes, number_format)
        
        # Promedio diario del mes
        promedio_diario = venta_mes['monto_total'] / dias_mes if dias_mes > 0 else 0
        monthly_sheet.write(row, 5, promedio_diario, currency_format)
        row += 1
    
    # Ajustar ancho de columnas
    monthly_sheet.set_column('A:A', 20)  # Mes/Año
    monthly_sheet.set_column('B:B', 12)  # Total Ventas
    monthly_sheet.set_column('C:D', 18)  # Montos
    monthly_sheet.set_column('E:F', 15)  # Días y Promedio
    
    # ===== HOJA 4: PRODUCTOS TOP =====
    products_sheet = workbook.add_worksheet('🏆 PRODUCTOS TOP')
    
    # Título
    products_sheet.merge_range('A1:G1', 'PRODUCTOS MÁS VENDIDOS - ANÁLISIS DE RENDIMIENTO', title_format)
    
    # Encabezados
    headers = ['Ranking', 'Producto', 'Categoría', 'Unidades Vendidas', 'Ingresos Totales', 'Precio Promedio', '% del Total']
    for col, header in enumerate(headers):
        products_sheet.write(2, col, header, header_format)
    
    # Calcular total de ingresos para porcentajes
    total_ingresos_productos = sum(p['total_ingresos'] for p in productos_top)
    
    # Datos
    row = 3
    for i, producto in enumerate(productos_top, 1):
        products_sheet.write(row, 0, i, number_format)  # Ranking
        products_sheet.write(row, 1, producto['producto__nombre'], cell_format)
        products_sheet.write(row, 2, producto['producto__categoria__nombre'] or 'Sin categoría', cell_format)
        products_sheet.write(row, 3, producto['total_vendido'], number_format)
        products_sheet.write(row, 4, producto['total_ingresos'], currency_format)
        
        # Precio promedio por unidad
        promedio = producto['total_ingresos'] / producto['total_vendido'] if producto['total_vendido'] > 0 else 0
        products_sheet.write(row, 5, promedio, currency_format)
        
        # Porcentaje del total
        porcentaje = (producto['total_ingresos'] / total_ingresos_productos * 100) if total_ingresos_productos > 0 else 0
        products_sheet.write(row, 6, porcentaje, percent_format)
        row += 1
    
    # Ajustar ancho de columnas
    products_sheet.set_column('A:A', 10)  # Ranking
    products_sheet.set_column('B:B', 35)  # Producto
    products_sheet.set_column('C:C', 20)  # Categoría
    products_sheet.set_column('D:D', 15)  # Unidades
    products_sheet.set_column('E:F', 18)  # Montos
    products_sheet.set_column('G:G', 12)  # Porcentaje
    
    # ===== HOJA 5: DETALLE DE VENTAS =====
    detail_sheet = workbook.add_worksheet('📋 DETALLE COMPLETO')
    
    # Título
    detail_sheet.merge_range('A1:H1', 'DETALLE COMPLETO DE VENTAS', title_format)
    
    # Encabezados
    headers = ['ID', 'Fecha', 'Cliente', 'Total', 'Tipo', 'Monto Abonado', 'Saldo Pendiente', 'Estado']
    for col, header in enumerate(headers):
        detail_sheet.write(2, col, header, header_format)
    
    # Obtener todas las ventas del período
    todas_ventas = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin)
    ).select_related('cliente').order_by('-fecha')
    
    # Datos
    row = 3
    for venta in todas_ventas:
        detail_sheet.write(row, 0, venta.id, number_format)
        # Convertir fecha a datetime sin timezone
        fecha_naive = convert_to_naive_datetime(venta.fecha)
        detail_sheet.write(row, 1, fecha_naive, date_format)
        detail_sheet.write(row, 2, venta.cliente.nombre if venta.cliente else 'Sin cliente', cell_format)
        detail_sheet.write(row, 3, venta.total, currency_format)
        
        # Tipo de venta
        tipo = 'Fiado' if venta.es_fiado else 'Contado'
        detail_sheet.write(row, 4, tipo, cell_format)
        
        # Monto abonado
        monto_abonado = venta.monto_abonado or 0
        detail_sheet.write(row, 5, monto_abonado, currency_format)
        
        # Saldo pendiente
        saldo_pendiente = venta.total - monto_abonado
        detail_sheet.write(row, 6, saldo_pendiente, currency_format)
        
        # Estado
        if venta.fecha_cancelacion:
            estado = 'CANCELADA'
            format_estado = negative_format
        elif saldo_pendiente > 0:
            estado = 'PENDIENTE'
            format_estado = negative_format
        else:
            estado = 'PAGADA'
            format_estado = positive_format
        
        detail_sheet.write(row, 7, estado, format_estado)
        row += 1
    
    # Ajustar ancho de columnas
    detail_sheet.set_column('A:A', 8)   # ID
    detail_sheet.set_column('B:B', 15)  # Fecha
    detail_sheet.set_column('C:C', 30)  # Cliente
    detail_sheet.set_column('D:F', 15)  # Montos
    detail_sheet.set_column('G:G', 15)  # Saldo
    detail_sheet.set_column('H:H', 12)  # Estado
    
    # ===== HOJA 6: GRÁFICOS Y ANÁLISIS =====
    if ventas_por_dia and productos_top:
        chart_sheet = workbook.add_worksheet('📊 GRÁFICOS')
        
        # Título
        chart_sheet.merge_range('A1:H1', 'GRÁFICOS Y ANÁLISIS VISUAL', title_format)
        
        # Gráfico de ventas por día
        chart = workbook.add_chart({'type': 'line'})
        chart.set_title({'name': 'Evolución de Ventas por Día'})
        chart.set_x_axis({'name': 'Fecha'})
        chart.set_y_axis({'name': 'Monto Total ($)'})
        chart.set_size({'width': 720, 'height': 400})
        
        # Agregar datos al gráfico
        chart.add_series({
            'name': 'Monto Total',
            'categories': f'=📅 VENTAS DIARIAS!$A$3:$A${2 + len(ventas_por_dia)}',
            'values': f'=📅 VENTAS DIARIAS!$C$3:$C${2 + len(ventas_por_dia)}',
            'line': {'color': '#4472C4', 'width': 3},
            'marker': {'type': 'circle', 'size': 6}
        })
        
        chart_sheet.insert_chart('A3', chart)
        
        # Gráfico de productos top
        chart2 = workbook.add_chart({'type': 'column'})
        chart2.set_title({'name': 'Top 10 Productos por Ingresos'})
        chart2.set_x_axis({'name': 'Productos'})
        chart2.set_y_axis({'name': 'Ingresos ($)'})
        chart2.set_size({'width': 720, 'height': 400})
        
        chart2.add_series({
            'name': 'Ingresos Totales',
            'categories': f'=🏆 PRODUCTOS TOP!$B$3:$B${2 + len(productos_top)}',
            'values': f'=🏆 PRODUCTOS TOP!$E$3:$E${2 + len(productos_top)}',
            'fill': {'color': '#70AD47'}
        })
        
        chart_sheet.insert_chart('A25', chart2)
        
        # Gráfico de distribución por tipo de venta
        chart3 = workbook.add_chart({'type': 'pie'})
        chart3.set_title({'name': 'Distribución por Tipo de Venta'})
        chart3.set_size({'width': 400, 'height': 300})
        
        # Crear datos para el gráfico circular en una hoja temporal
        chart_data_sheet = workbook.add_worksheet('Chart Data')
        chart_data_sheet.write('A1', 'Tipo de Venta', header_format)
        chart_data_sheet.write('B1', 'Cantidad', header_format)
        chart_data_sheet.write('A2', 'Contado', cell_format)
        chart_data_sheet.write('B2', ventas_contado, number_format)
        chart_data_sheet.write('A3', 'Fiado', cell_format)
        chart_data_sheet.write('B3', ventas_fiado, number_format)
        
        # Ocultar la hoja de datos del gráfico
        chart_data_sheet.hide()
        
        # Crear datos para el gráfico circular
        chart3.add_series({
            'name': 'Tipo de Venta',
            'categories': '=Chart Data!$A$2:$A$3',
            'values': '=Chart Data!$B$2:$B$3',
            'data_labels': {'percentage': True}
        })
        
        chart_sheet.insert_chart('A50', chart3)
    
    # Cerrar el workbook
    workbook.close()
    
    # Preparar la respuesta HTTP
    output.seek(0)
    filename = f'Reporte_Ventas_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response 