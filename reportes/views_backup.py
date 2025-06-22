from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, DecimalField, Q, Case, When, Max
from django.db.models.functions import TruncDate, ExtractMonth
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta, datetime
from calendar import monthrange
import csv
import xlsxwriter
import io

from productos.models import Producto
from ventas.models import Venta, DetalleVenta
from clientes.models import Cliente
from proveedores.models import Proveedor
from categorias.models import Categoria
from .models import ConfiguracionReporte, HistorialReporte

@login_required
def lista_reportes(request):
    configuraciones = ConfiguracionReporte.objects.filter(usuario=request.user)
    ultimos_reportes = HistorialReporte.objects.filter(usuario=request.user)[:5]
    
    context = {
        'configuraciones': configuraciones,
        'ultimos_reportes': ultimos_reportes,
    }
    return render(request, 'reportes/lista_reportes.html', context)

@login_required
def reporte_productos(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Productos con stock bajo
    productos_bajo_stock = Producto.objects.filter(
        stock_actual__lte=F('stock_minimo')
    ).select_related('categoria')
    
    # Productos más vendidos
    productos_mas_vendidos = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'producto__nombre',
        'producto__id',
        'producto__categoria__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario')),
        precio_promedio=Avg('precio_unitario')
    ).order_by('-total_vendido')[:10]
    
    # Rotación de inventario
    productos_rotacion = Producto.objects.annotate(
        ventas_totales=Sum('detalleventa__cantidad'),
        valor_inventario=ExpressionWrapper(
            F('stock_actual') * F('precio'),
            output_field=DecimalField()
        )
    ).filter(ventas_totales__gt=0)
    
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_productos_excel(
            request,
            productos_bajo_stock,
            productos_mas_vendidos,
            productos_rotacion,
            fecha_inicio,
            fecha_fin
        )
    
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
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Ventas por día
    ventas_por_dia = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin)
    ).annotate(
        fecha_dia=TruncDate('fecha')
    ).values('fecha_dia').annotate(
        total_ventas=Sum('total'),
        cantidad_ventas=Count('id')
    ).order_by('fecha_dia')
    
    # Ventas por mes
    ventas_por_mes = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin)
    ).annotate(
        mes=ExtractMonth('fecha')
    ).values('mes').annotate(
        total_ventas=Sum('total'),
        cantidad_ventas=Count('id')
    ).order_by('mes')
    
    # Productos más vendidos en el período
    productos_top = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario'))
    ).order_by('-total_vendido')[:5]
    
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_ventas_excel(
            request,
            ventas_por_dia,
            ventas_por_mes,
            productos_top,
            fecha_inicio,
            fecha_fin
        )
    
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
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Clientes con más compras
    clientes_top = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin),
        cliente__isnull=False
    ).values(
        'cliente__nombre',
        'cliente__documento'
    ).annotate(
        total_compras=Count('id'),
        total_gastado=Sum('total'),
        promedio_compra=Avg('total'),
        ventas_fiado=Count('id', filter=Q(es_fiado=True))
    ).order_by('-total_gastado')
    
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_clientes_excel(
            request,
            clientes_top,
            fecha_inicio,
            fecha_fin
        )
    
    context = {
        'clientes_top': clientes_top,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/reporte_clientes.html', context)

@login_required
def reporte_proveedores(request):
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
        productos_bajo_stock=Count('id', filter=Q(
            Q(stock_actual__lte=F('stock_minimo')) & Q(stock_minimo__isnull=False)
        ) | Q(stock_actual__lte=5) & Q(stock_minimo__isnull=True)
        )),
        productos_sin_stock=Count('id', filter=Q(stock_actual=0)),
        ultima_venta=Max('detalleventa__venta__fecha')
    ).order_by('-cantidad_productos')
    
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
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Fiados pendientes
    fiados_pendientes = Venta.objects.filter(
        es_fiado=True,
        fecha__range=(fecha_inicio, fecha_fin)
    ).select_related('cliente').order_by('-fecha')
    
    # Clientes con más fiados
    clientes_fiados = Venta.objects.filter(
        es_fiado=True,
        fecha__range=(fecha_inicio, fecha_fin),
        cliente__isnull=False
    ).values(
        'cliente__nombre',
        'cliente__documento'
    ).annotate(
        total_fiados=Count('id'),
        monto_total=Sum('total'),
        promedio_fiado=Avg('total')
    ).order_by('-monto_total')
    
    # Análisis de antigüedad de fiados
    fiados_antiguedad = Venta.objects.filter(
        es_fiado=True,
        fecha__range=(fecha_inicio, fecha_fin)
    ).annotate(
        dias_antiguedad=ExpressionWrapper(
            timezone.now() - F('fecha'),
            output_field=DecimalField()
        )
    ).values(
        'cliente__nombre'
    ).annotate(
        fiados_antiguos=Count('id', filter=Q(dias_antiguedad__gt=30)),
        fiados_recientes=Count('id', filter=Q(dias_antiguedad__lte=30)),
        monto_antiguo=Sum('total', filter=Q(dias_antiguedad__gt=30)),
        monto_reciente=Sum('total', filter=Q(dias_antiguedad__lte=30))
    ).filter(fiados_antiguos__gt=0)
    
    # Resumen de fiados
    total_fiados = fiados_pendientes.count()
    monto_total_fiados = fiados_pendientes.aggregate(total=Sum('total'))['total'] or 0
    promedio_fiado_general = monto_total_fiados / total_fiados if total_fiados > 0 else 0
    
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_fiados_excel(
            request,
            fiados_pendientes,
            clientes_fiados,
            fiados_antiguedad,
            fecha_inicio,
            fecha_fin
        )
    
    context = {
        'fiados_pendientes': fiados_pendientes,
        'clientes_fiados': clientes_fiados,
        'fiados_antiguedad': fiados_antiguedad,
        'total_fiados': total_fiados,
        'monto_total_fiados': monto_total_fiados,
        'promedio_fiado_general': promedio_fiado_general,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/reporte_fiados.html', context)

@login_required
def reporte_categorias(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    if fecha_inicio and fecha_fin:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    else:
        fecha_fin = timezone.now()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Análisis de categorías por ventas
    categorias_ventas = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'producto__categoria__nombre',
        'producto__categoria__id'
    ).annotate(
        total_productos=Count('producto__id', distinct=True),
        total_vendido=Sum('cantidad'),
        total_ingresos=Sum(F('cantidad') * F('precio_unitario')),
        costo_total=Sum(F('cantidad') * F('producto__precio')),
        margen_ganancia=ExpressionWrapper(
            Sum(F('cantidad') * F('precio_unitario')) - 
            Sum(F('cantidad') * F('producto__precio')),
            output_field=DecimalField()
        )
    ).order_by('-total_ingresos')
    
    # Productos por categoría
    productos_por_categoria = Producto.objects.filter(
        categoria__isnull=False
    ).values(
        'categoria__nombre'
    ).annotate(
        cantidad_productos=Count('id'),
        stock_total=Sum('stock_actual'),
        valor_inventario=Sum(F('stock_actual') * F('precio')),
        productos_bajo_stock=Count('id', filter=Q(stock_actual__lte=F('stock_minimo')))
    ).order_by('-cantidad_productos')
    
    # Categorías con mejor margen
    categorias_margen = DetalleVenta.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'producto__categoria__nombre'
    ).annotate(
        margen_promedio=ExpressionWrapper(
            (Sum(F('cantidad') * F('precio_unitario')) - 
             Sum(F('cantidad') * F('producto__precio'))) / 
            Sum(F('cantidad') * F('precio_unitario')) * 100,
            output_field=DecimalField()
        )
    ).order_by('-margen_promedio')
    
    # Rotación de inventario por categoría
    rotacion_categorias = Producto.objects.filter(
        categoria__isnull=False,
        detalleventa__venta__fecha__range=(fecha_inicio, fecha_fin)
    ).values(
        'categoria__nombre'
    ).annotate(
        productos_vendidos=Count('detalleventa__id'),
        unidades_vendidas=Sum('detalleventa__cantidad'),
        valor_vendido=Sum(F('detalleventa__cantidad') * F('detalleventa__precio_unitario'))
    ).order_by('-unidades_vendidas')
    
    if request.GET.get('formato') == 'excel':
        return exportar_reporte_categorias_excel(
            request,
            categorias_ventas,
            productos_por_categoria,
            categorias_margen,
            rotacion_categorias,
            fecha_inicio,
            fecha_fin
        )
    
    context = {
        'categorias_ventas': categorias_ventas,
        'productos_por_categoria': productos_por_categoria,
        'categorias_margen': categorias_margen,
        'rotacion_categorias': rotacion_categorias,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
    }
    return render(request, 'reportes/reporte_categorias.html', context)

def exportar_reporte_productos_excel(request, productos_bajo_stock, productos_mas_vendidos, productos_rotacion, fecha_inicio, fecha_fin):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
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
    
    # Formato para fechas
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # Formato para totales
    total_format = workbook.add_format({
        'bold': True,
        'bg_color': '#F18F01',
        'font_color': 'white',
        'border': 1,
        'num_format': '#,##0.00'
    })
    
    # Obtener todos los productos para el inventario completo
    todos_productos = Producto.objects.select_related('categoria', 'proveedor').all()
    
    # ===== HOJA 1: INVENTARIO COMPLETO =====
    worksheet_inventario = workbook.add_worksheet('Inventario Completo')
    worksheet_inventario.set_column('A:A', 8)   # ID
    worksheet_inventario.set_column('B:B', 25)  # Nombre
    worksheet_inventario.set_column('C:C', 15)  # Categoría
    worksheet_inventario.set_column('D:D', 20)  # Descripción
    worksheet_inventario.set_column('E:E', 15)  # Proveedor
    worksheet_inventario.set_column('F:F', 12)  # Stock Actual
    worksheet_inventario.set_column('G:G', 12)  # Stock Mínimo
    worksheet_inventario.set_column('H:H', 12)  # Stock Inicial
    worksheet_inventario.set_column('I:I', 12)  # Precio
    worksheet_inventario.set_column('J:J', 15)  # Valor Inventario
    worksheet_inventario.set_column('K:K', 10)  # Estado
    worksheet_inventario.set_column('L:L', 12)  # Fecha Creación
    worksheet_inventario.set_column('M:M', 12)  # Última Actualización
    
    # Título principal
    worksheet_inventario.merge_range('A1:M1', 'INVENTARIO COMPLETO DE PRODUCTOS', header_format)
    worksheet_inventario.merge_range('A2:M2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['ID', 'Nombre', 'Categoría', 'Descripción', 'Proveedor', 'Stock Actual', 'Stock Mínimo', 'Stock Inicial', 'Precio', 'Valor Inventario', 'Estado', 'Fecha Creación', 'Última Actualización']
    for col, header in enumerate(headers):
        worksheet_inventario.write(3, col, header, header_format)
    
    # Variables para totales
    total_stock_actual = 0
    total_stock_minimo = 0
    total_stock_inicial = 0
    total_valor_inventario = 0
    total_productos_bajo_stock = 0
    total_productos_criticos = 0
    total_productos_activos = 0
    
    row = 4
    for producto in todos_productos:
        valor_inventario = producto.stock_actual * producto.precio
        
        if producto.stock_actual <= producto.stock_minimo:
            estado = "CRÍTICO" if producto.stock_actual == 0 else "BAJO"
            total_productos_bajo_stock += 1
            if producto.stock_actual == 0:
                total_productos_criticos += 1
        else:
            estado = "NORMAL"
        
        if producto.activo:
            total_productos_activos += 1
            
        # Acumular totales
        total_stock_actual += producto.stock_actual
        total_stock_minimo += producto.stock_minimo
        total_stock_inicial += producto.stock_inicial
        total_valor_inventario += valor_inventario
        
        # Escribir datos
        worksheet_inventario.write(row, 0, producto.id)
        worksheet_inventario.write(row, 1, producto.nombre)
        worksheet_inventario.write(row, 2, producto.categoria.nombre if producto.categoria else "Sin categoría")
        worksheet_inventario.write(row, 3, producto.descripcion[:50] + "..." if len(producto.descripcion) > 50 else producto.descripcion)
        worksheet_inventario.write(row, 4, producto.proveedor.nombre if producto.proveedor else "Sin proveedor")
        worksheet_inventario.write(row, 5, producto.stock_actual)
        worksheet_inventario.write(row, 6, producto.stock_minimo)
        worksheet_inventario.write(row, 7, producto.stock_inicial)
        worksheet_inventario.write(row, 8, float(producto.precio), number_format)
        worksheet_inventario.write(row, 9, float(valor_inventario), number_format)
        worksheet_inventario.write(row, 10, estado)
        worksheet_inventario.write(row, 11, producto.fecha_creacion.replace(tzinfo=None), date_format)
        worksheet_inventario.write(row, 12, producto.fecha_actualizacion.replace(tzinfo=None), date_format)
        row += 1
    
    # Fila de totales
    worksheet_inventario.write(row, 0, "TOTALES", total_format)
    worksheet_inventario.write(row, 1, f"{len(todos_productos)} productos", total_format)
    worksheet_inventario.write(row, 5, total_stock_actual, total_format)
    worksheet_inventario.write(row, 6, total_stock_minimo, total_format)
    worksheet_inventario.write(row, 7, total_stock_inicial, total_format)
    worksheet_inventario.write(row, 9, float(total_valor_inventario), total_format)
    worksheet_inventario.write(row, 10, f"{total_productos_bajo_stock} bajo stock", total_format)
    
    # ===== HOJA 2: PRODUCTOS BAJO STOCK =====
    if productos_bajo_stock.exists():
        worksheet_stock = workbook.add_worksheet('Productos Bajo Stock')
        worksheet_stock.set_column('A:A', 8)
        worksheet_stock.set_column('B:B', 25)
        worksheet_stock.set_column('C:C', 15)
        worksheet_stock.set_column('D:D', 15)
        worksheet_stock.set_column('E:E', 12)
        worksheet_stock.set_column('F:F', 12)
        worksheet_stock.set_column('G:G', 15)
        worksheet_stock.set_column('H:H', 20)
        
        worksheet_stock.merge_range('A1:H1', 'PRODUCTOS CON STOCK BAJO - REABASTECIMIENTO URGENTE', header_format)
        
        headers = ['ID', 'Nombre', 'Categoría', 'Proveedor', 'Stock Actual', 'Stock Mínimo', 'Unidades Faltantes', 'Valor Faltante']
        for col, header in enumerate(headers):
            worksheet_stock.write(2, col, header, header_format)
        
        total_stock_bajo_actual = 0
        total_stock_bajo_minimo = 0
        total_unidades_faltantes = 0
        total_valor_faltante = 0
        
        row = 3
        for producto in productos_bajo_stock:
            unidades_faltantes = producto.stock_minimo - producto.stock_actual
            valor_faltante = unidades_faltantes * producto.precio
            
            total_stock_bajo_actual += producto.stock_actual
            total_stock_bajo_minimo += producto.stock_minimo
            total_unidades_faltantes += unidades_faltantes
            total_valor_faltante += valor_faltante
            
            worksheet_stock.write(row, 0, producto.id)
            worksheet_stock.write(row, 1, producto.nombre)
            worksheet_stock.write(row, 2, producto.categoria.nombre if producto.categoria else "Sin categoría")
            worksheet_stock.write(row, 3, producto.proveedor.nombre if producto.proveedor else "Sin proveedor")
            worksheet_stock.write(row, 4, producto.stock_actual)
            worksheet_stock.write(row, 5, producto.stock_minimo)
            worksheet_stock.write(row, 6, unidades_faltantes)
            worksheet_stock.write(row, 7, float(valor_faltante), number_format)
            row += 1
        
        # Totales
        worksheet_stock.write(row, 0, "TOTALES", total_format)
        worksheet_stock.write(row, 1, f"{len(productos_bajo_stock)} productos", total_format)
        worksheet_stock.write(row, 4, total_stock_bajo_actual, total_format)
        worksheet_stock.write(row, 5, total_stock_bajo_minimo, total_format)
        worksheet_stock.write(row, 6, total_unidades_faltantes, total_format)
        worksheet_stock.write(row, 7, float(total_valor_faltante), total_format)
    
    # ===== HOJA 3: PRODUCTOS MÁS VENDIDOS =====
    if productos_mas_vendidos:
        worksheet_vendidos = workbook.add_worksheet('Productos Más Vendidos')
        worksheet_vendidos.set_column('A:A', 25)
        worksheet_vendidos.set_column('B:B', 8)
        worksheet_vendidos.set_column('C:C', 15)
        worksheet_vendidos.set_column('D:D', 15)
        worksheet_vendidos.set_column('E:E', 15)
        worksheet_vendidos.set_column('F:F', 15)
        worksheet_vendidos.set_column('G:G', 15)
        
        worksheet_vendidos.merge_range('A1:G1', 'PRODUCTOS MÁS VENDIDOS - ANÁLISIS DE VENTAS', header_format)
        worksheet_vendidos.merge_range('A2:G2', f'Período de análisis: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['Producto', 'ID', 'Categoría', 'Cantidad Vendida', 'Total Ingresos', 'Precio Promedio', '% del Total']
        for col, header in enumerate(headers):
            worksheet_vendidos.write(3, col, header, header_format)
        
        total_cantidad_vendida = 0
        total_ingresos = 0
        
        for producto in productos_mas_vendidos:
            total_cantidad_vendida += producto['total_vendido']
            total_ingresos += float(producto['total_ingresos'])
        
        row = 4
        for producto in productos_mas_vendidos:
            porcentaje = (float(producto['total_ingresos']) / total_ingresos * 100) if total_ingresos > 0 else 0
            
            worksheet_vendidos.write(row, 0, producto['producto__nombre'])
            worksheet_vendidos.write(row, 1, producto['producto__id'])
            worksheet_vendidos.write(row, 2, producto['producto__categoria__nombre'] if producto['producto__categoria__nombre'] else "Sin categoría")
            worksheet_vendidos.write(row, 3, producto['total_vendido'])
            worksheet_vendidos.write(row, 4, float(producto['total_ingresos']), number_format)
            worksheet_vendidos.write(row, 5, float(producto['precio_promedio']), number_format)
            worksheet_vendidos.write(row, 6, f"{porcentaje:.1f}%")
            row += 1
        
        # Totales
        worksheet_vendidos.write(row, 0, "TOTALES", total_format)
        worksheet_vendidos.write(row, 1, f"{len(productos_mas_vendidos)} productos", total_format)
        worksheet_vendidos.write(row, 3, total_cantidad_vendida, total_format)
        worksheet_vendidos.write(row, 4, float(total_ingresos), total_format)
        worksheet_vendidos.write(row, 5, f"Promedio: ${total_ingresos/total_cantidad_vendida:.2f}" if total_cantidad_vendida > 0 else "N/A", total_format)
        worksheet_vendidos.write(row, 6, "100.0%", total_format)
    
    # ===== HOJA 4: ANÁLISIS DE CLIENTES =====
    # Obtener datos de clientes
    ventas_periodo = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin))
    clientes_activos = ventas_periodo.values('cliente__nombre', 'cliente__documento').annotate(
        total_compras=Count('id'),
        total_gastado=Sum('total'),
        promedio_compra=Avg('total'),
        ventas_fiado=Count('id', filter=Q(es_fiado=True))
    ).filter(cliente__isnull=False).order_by('-total_gastado')
    
    if clientes_activos:
        worksheet_clientes = workbook.add_worksheet('Análisis de Clientes')
        worksheet_clientes.set_column('A:A', 25)
        worksheet_clientes.set_column('B:B', 15)
        worksheet_clientes.set_column('C:C', 12)
        worksheet_clientes.set_column('D:D', 15)
        worksheet_clientes.set_column('E:E', 15)
        worksheet_clientes.set_column('F:F', 12)
        
        worksheet_clientes.merge_range('A1:F1', 'ANÁLISIS DE CLIENTES - COMPORTAMIENTO DE COMPRA', header_format)
        worksheet_clientes.merge_range('A2:F2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['Cliente', 'Documento', 'Total Compras', 'Total Gastado', 'Promedio Compra', 'Ventas Fiado']
        for col, header in enumerate(headers):
            worksheet_clientes.write(3, col, header, header_format)
        
        total_clientes = 0
        total_compras = 0
        total_gastado = 0
        total_fiados = 0
        
        row = 4
        for cliente in clientes_activos:
            total_clientes += 1
            total_compras += cliente['total_compras']
            total_gastado += float(cliente['total_gastado'])
            total_fiados += cliente['ventas_fiado']
            
            worksheet_clientes.write(row, 0, cliente['cliente__nombre'])
            worksheet_clientes.write(row, 1, cliente['cliente__documento'])
            worksheet_clientes.write(row, 2, cliente['total_compras'])
            worksheet_clientes.write(row, 3, float(cliente['total_gastado']), number_format)
            worksheet_clientes.write(row, 4, float(cliente['promedio_compra']), number_format)
            worksheet_clientes.write(row, 5, cliente['ventas_fiado'])
            row += 1
        
        # Totales
        worksheet_clientes.write(row, 0, "TOTALES", total_format)
        worksheet_clientes.write(row, 1, f"{total_clientes} clientes", total_format)
        worksheet_clientes.write(row, 2, total_compras, total_format)
        worksheet_clientes.write(row, 3, float(total_gastado), total_format)
        worksheet_clientes.write(row, 4, f"Promedio: ${total_gastado/total_clientes:.2f}" if total_clientes > 0 else "N/A", total_format)
        worksheet_clientes.write(row, 5, total_fiados, total_format)
    
    # ===== HOJA 5: RESUMEN EJECUTIVO =====
    worksheet_resumen = workbook.add_worksheet('Resumen Ejecutivo')
    worksheet_resumen.set_column('A:A', 30)
    worksheet_resumen.set_column('B:B', 20)
    
    worksheet_resumen.merge_range('A1:B1', 'RESUMEN EJECUTIVO - TRADE INVENTORY', header_format)
    worksheet_resumen.merge_range('A2:B2', f'Reporte generado el: {timezone.now().replace(tzinfo=None).strftime("%d/%m/%Y %H:%M")}', subheader_format)
    
    # Métricas principales
    total_productos = todos_productos.count()
    productos_sin_stock = todos_productos.filter(stock_actual=0).count()
    productos_inactivos = todos_productos.filter(activo=False).count()
    
    # Análisis de ventas
    total_ventas_periodo = ventas_periodo.count()
    ventas_fiado = ventas_periodo.filter(es_fiado=True).count()
    total_ventas_periodo_valor = ventas_periodo.aggregate(total=Sum('total'))['total'] or 0
    
    resumen_data = [
        ['MÉTRICAS DE INVENTARIO', ''],
        ['Total de Productos', total_productos],
        ['Productos Activos', total_productos_activos],
        ['Productos Inactivos', productos_inactivos],
        ['Productos con Bajo Stock', total_productos_bajo_stock],
        ['Productos Sin Stock (Crítico)', total_productos_criticos],
        ['Productos Sin Stock', productos_sin_stock],
        ['', ''],
        ['VALORES DE INVENTARIO', ''],
        ['Stock Total Actual', total_stock_actual],
        ['Stock Total Mínimo', total_stock_minimo],
        ['Stock Total Inicial', total_stock_inicial],
        ['Valor Total del Inventario', total_valor_inventario],
        ['', ''],
        ['MÉTRICAS DE VENTAS', ''],
        ['Total Ventas en Período', total_ventas_periodo],
        ['Ventas Normales', total_ventas_periodo - ventas_fiado],
        ['Ventas a Fiado', ventas_fiado],
        ['Valor Total Ventas', total_ventas_periodo_valor],
        ['', ''],
        ['INFORMACIÓN DEL REPORTE', ''],
        ['Período Analizado', f"{fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"],
        ['Días del Período', (fecha_fin - fecha_inicio).days + 1],
        ['Generado por', request.user.username if request.user.is_authenticated else 'Sistema'],
    ]
    
    row = 3
    for metrica, valor in resumen_data:
        if metrica == '':
            row += 1
            continue
        if metrica in ['MÉTRICAS DE INVENTARIO', 'VALORES DE INVENTARIO', 'MÉTRICAS DE VENTAS', 'INFORMACIÓN DEL REPORTE']:
            worksheet_resumen.write(row, 0, metrica, subheader_format)
            worksheet_resumen.write(row, 1, valor, subheader_format)
        else:
            worksheet_resumen.write(row, 0, metrica)
            if isinstance(valor, (int, float)) and metrica in ['Valor Total del Inventario', 'Valor Total Ventas', 'Stock Total Actual', 'Stock Total Mínimo', 'Stock Total Inicial']:
                worksheet_resumen.write(row, 1, float(valor), number_format)
            else:
                worksheet_resumen.write(row, 1, valor)
        row += 1
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_productos_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    # Guardar en historial
    if hasattr(request, 'user'):
        config = ConfiguracionReporte.objects.create(
            nombre=f"Reporte de Productos {fecha_inicio.strftime('%Y-%m-%d')} al {fecha_fin.strftime('%Y-%m-%d')}",
            tipo_reporte='productos',
            periodo='personalizado',
            usuario=request.user
        )
        HistorialReporte.objects.create(
            configuracion=config,
            usuario=request.user
        )
    
    return response

def exportar_reporte_ventas_excel(request, ventas_por_dia, ventas_por_mes, productos_top, fecha_inicio, fecha_fin):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
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
    
    # Formato para fechas
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # Formato para totales
    total_format = workbook.add_format({
        'bold': True,
        'bg_color': '#F18F01',
        'font_color': 'white',
        'border': 1,
        'num_format': '#,##0.00'
    })
    
    # Obtener datos adicionales para el análisis
    ventas_periodo = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin))
    total_ventas_periodo = ventas_periodo.count()
    total_valor_periodo = ventas_periodo.aggregate(total=Sum('total'))['total'] or 0
    ventas_fiado = ventas_periodo.filter(es_fiado=True).count()
    ventas_normal = total_ventas_periodo - ventas_fiado
    valor_fiado = ventas_periodo.filter(es_fiado=True).aggregate(total=Sum('total'))['total'] or 0
    valor_normal = total_valor_periodo - valor_fiado
    
    # ===== HOJA 1: RESUMEN EJECUTIVO =====
    worksheet_resumen = workbook.add_worksheet('Resumen Ejecutivo')
    worksheet_resumen.set_column('A:A', 35)
    worksheet_resumen.set_column('B:B', 25)
    
    worksheet_resumen.merge_range('A1:B1', 'RESUMEN EJECUTIVO DE VENTAS - TRADE INVENTORY', header_format)
    worksheet_resumen.merge_range('A2:B2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    worksheet_resumen.merge_range('A3:B3', f'Reporte generado el: {timezone.now().replace(tzinfo=None).strftime("%d/%m/%Y %H:%M")}', subheader_format)
    
    resumen_data = [
        ['MÉTRICAS GENERALES', ''],
        ['Total de Ventas', total_ventas_periodo],
        ['Valor Total de Ventas', total_valor_periodo],
        ['Promedio por Venta', total_valor_periodo / total_ventas_periodo if total_ventas_periodo > 0 else 0],
        ['', ''],
        ['ANÁLISIS POR TIPO DE VENTA', ''],
        ['Ventas Normales', ventas_normal],
        ['Ventas a Fiado', ventas_fiado],
        ['Valor Ventas Normales', valor_normal],
        ['Valor Ventas a Fiado', valor_fiado],
        ['Porcentaje Ventas Fiado', f"{(ventas_fiado/total_ventas_periodo*100):.1f}%" if total_ventas_periodo > 0 else "0%"],
        ['', ''],
        ['PERÍODO DE ANÁLISIS', ''],
        ['Días del Período', (fecha_fin - fecha_inicio).days + 1],
        ['Promedio Ventas por Día', f"{total_ventas_periodo/((fecha_fin - fecha_inicio).days + 1):.1f}" if (fecha_fin - fecha_inicio).days > 0 else "0"],
        ['Promedio Valor por Día', f"{total_valor_periodo/((fecha_fin - fecha_inicio).days + 1):.2f}" if (fecha_fin - fecha_inicio).days > 0 else "0"],
    ]
    
    row = 4
    for metrica, valor in resumen_data:
        if metrica == '':
            row += 1
            continue
        if metrica in ['MÉTRICAS GENERALES', 'ANÁLISIS POR TIPO DE VENTA', 'PERÍODO DE ANÁLISIS']:
            worksheet_resumen.write(row, 0, metrica, subheader_format)
            worksheet_resumen.write(row, 1, valor, subheader_format)
        else:
            worksheet_resumen.write(row, 0, metrica)
            if isinstance(valor, (int, float)) and metrica in ['Valor Total de Ventas', 'Promedio por Venta', 'Valor Ventas Normales', 'Valor Ventas a Fiado', 'Promedio Valor por Día']:
                worksheet_resumen.write(row, 1, float(valor), number_format)
            else:
                worksheet_resumen.write(row, 1, valor)
        row += 1
    
    # ===== HOJA 2: VENTAS POR DÍA =====
    if ventas_por_dia:
        worksheet_dia = workbook.add_worksheet('Ventas por Día')
        worksheet_dia.set_column('A:A', 15)
        worksheet_dia.set_column('B:B', 20)
        worksheet_dia.set_column('C:C', 20)
        worksheet_dia.set_column('D:D', 20)
        worksheet_dia.set_column('E:E', 20)
        
        worksheet_dia.merge_range('A1:E1', 'ANÁLISIS DE VENTAS POR DÍA', header_format)
        worksheet_dia.merge_range('A2:E2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['Fecha', 'Cantidad Ventas', 'Total Vendido', 'Promedio por Venta', 'Día de la Semana']
        for col, header in enumerate(headers):
            worksheet_dia.write(3, col, header, header_format)
        
        total_ventas_dia = 0
        total_valor_dia = 0
        
        row = 4
        for venta in ventas_por_dia:
            fecha = venta['fecha_dia']
            dia_semana = fecha.strftime('%A') if hasattr(fecha, 'strftime') else 'N/A'
            promedio = venta['total_ventas'] / venta['cantidad_ventas'] if venta['cantidad_ventas'] > 0 else 0
            
            total_ventas_dia += venta['cantidad_ventas']
            total_valor_dia += float(venta['total_ventas'])
            
            worksheet_dia.write(row, 0, fecha, date_format)
            worksheet_dia.write(row, 1, venta['cantidad_ventas'])
            worksheet_dia.write(row, 2, float(venta['total_ventas']), number_format)
            worksheet_dia.write(row, 3, float(promedio), number_format)
            worksheet_dia.write(row, 4, dia_semana)
            row += 1
        
        # Totales
        worksheet_dia.write(row, 0, "TOTALES", total_format)
        worksheet_dia.write(row, 1, total_ventas_dia, total_format)
        worksheet_dia.write(row, 2, float(total_valor_dia), total_format)
        worksheet_dia.write(row, 3, f"Promedio: ${total_valor_dia/total_ventas_dia:.2f}" if total_ventas_dia > 0 else "N/A", total_format)
    
    # ===== HOJA 3: VENTAS POR MES =====
    if ventas_por_mes:
        worksheet_mes = workbook.add_worksheet('Ventas por Mes')
        worksheet_mes.set_column('A:A', 15)
        worksheet_mes.set_column('B:B', 20)
        worksheet_mes.set_column('C:C', 20)
        worksheet_mes.set_column('D:D', 20)
        
        worksheet_mes.merge_range('A1:D1', 'ANÁLISIS DE VENTAS POR MES', header_format)
        worksheet_mes.merge_range('A2:D2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['Mes', 'Cantidad Ventas', 'Total Vendido', 'Promedio por Venta']
        for col, header in enumerate(headers):
            worksheet_mes.write(3, col, header, header_format)
        
        total_ventas_mes = 0
        total_valor_mes = 0
        
        row = 4
        for venta in ventas_por_mes:
            mes_nombre = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }.get(venta['mes'], f'Mes {venta["mes"]}')
            
            promedio = venta['total_ventas'] / venta['cantidad_ventas'] if venta['cantidad_ventas'] > 0 else 0
            
            total_ventas_mes += venta['cantidad_ventas']
            total_valor_mes += float(venta['total_ventas'])
            
            worksheet_mes.write(row, 0, mes_nombre)
            worksheet_mes.write(row, 1, venta['cantidad_ventas'])
            worksheet_mes.write(row, 2, float(venta['total_ventas']), number_format)
            worksheet_mes.write(row, 3, float(promedio), number_format)
            row += 1
        
        # Totales
        worksheet_mes.write(row, 0, "TOTALES", total_format)
        worksheet_mes.write(row, 1, total_ventas_mes, total_format)
        worksheet_mes.write(row, 2, float(total_valor_mes), total_format)
        worksheet_mes.write(row, 3, f"Promedio: ${total_valor_mes/total_ventas_mes:.2f}" if total_ventas_mes > 0 else "N/A", total_format)
    
    # ===== HOJA 4: PRODUCTOS MÁS VENDIDOS =====
    if productos_top:
        worksheet_productos = workbook.add_worksheet('Productos Más Vendidos')
        worksheet_productos.set_column('A:A', 30)
        worksheet_productos.set_column('B:B', 15)
        worksheet_productos.set_column('C:C', 20)
        worksheet_productos.set_column('D:D', 20)
        worksheet_productos.set_column('E:E', 15)
        
        worksheet_productos.merge_range('A1:E1', 'PRODUCTOS MÁS VENDIDOS - ANÁLISIS DE RENDIMIENTO', header_format)
        worksheet_productos.merge_range('A2:E2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['Producto', 'Cantidad Vendida', 'Total Ingresos', 'Porcentaje del Total', 'Ranking']
        for col, header in enumerate(headers):
            worksheet_productos.write(3, col, header, header_format)
        
        total_cantidad_vendida = 0
        total_ingresos = 0
        
        for producto in productos_top:
            total_cantidad_vendida += producto['total_vendido']
            total_ingresos += float(producto['total_ingresos'])
        
        row = 4
        for i, producto in enumerate(productos_top, 1):
            porcentaje = (float(producto['total_ingresos']) / total_ingresos * 100) if total_ingresos > 0 else 0
            
            worksheet_productos.write(row, 0, producto['producto__nombre'])
            worksheet_productos.write(row, 1, producto['total_vendido'])
            worksheet_productos.write(row, 2, float(producto['total_ingresos']), number_format)
            worksheet_productos.write(row, 3, f"{porcentaje:.1f}%")
            worksheet_productos.write(row, 4, f"#{i}")
            row += 1
        
        # Totales
        worksheet_productos.write(row, 0, "TOTALES", total_format)
        worksheet_productos.write(row, 1, total_cantidad_vendida, total_format)
        worksheet_productos.write(row, 2, float(total_ingresos), total_format)
        worksheet_productos.write(row, 3, "100.0%", total_format)
        worksheet_productos.write(row, 4, f"{len(productos_top)} productos", total_format)
    
    # ===== HOJA 5: DETALLE DE VENTAS =====
    # Obtener todas las ventas del período con detalles
    ventas_detalladas = Venta.objects.filter(
        fecha__range=(fecha_inicio, fecha_fin)
    ).select_related('cliente').prefetch_related('detalles__producto').order_by('-fecha')
    
    if ventas_detalladas:
        worksheet_detalle = workbook.add_worksheet('Detalle de Ventas')
        worksheet_detalle.set_column('A:A', 10)
        worksheet_detalle.set_column('B:B', 20)
        worksheet_detalle.set_column('C:C', 25)
        worksheet_detalle.set_column('D:D', 15)
        worksheet_detalle.set_column('E:E', 15)
        worksheet_detalle.set_column('F:F', 15)
        worksheet_detalle.set_column('G:G', 15)
        
        worksheet_detalle.merge_range('A1:G1', 'DETALLE COMPLETO DE VENTAS', header_format)
        worksheet_detalle.merge_range('A2:G2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['ID Venta', 'Fecha', 'Cliente', 'Tipo', 'Total', 'Productos', 'Estado']
        for col, header in enumerate(headers):
            worksheet_detalle.write(3, col, header, header_format)
        
        row = 4
        for venta in ventas_detalladas:
            tipo_venta = "Fiado" if venta.es_fiado else "Normal"
            cliente_nombre = venta.cliente.nombre if venta.cliente else "Cliente General"
            productos_count = venta.detalles.count()
            
            worksheet_detalle.write(row, 0, venta.id)
            worksheet_detalle.write(row, 1, venta.fecha.replace(tzinfo=None), date_format)
            worksheet_detalle.write(row, 2, cliente_nombre)
            worksheet_detalle.write(row, 3, tipo_venta)
            worksheet_detalle.write(row, 4, float(venta.total), number_format)
            worksheet_detalle.write(row, 5, productos_count)
            worksheet_detalle.write(row, 6, "Completada")
            row += 1
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_ventas_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    return response

def exportar_reporte_clientes_excel(request, clientes_top, fecha_inicio, fecha_fin):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
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
    
    # Formato para fechas
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # Formato para totales
    total_format = workbook.add_format({
        'bold': True,
        'bg_color': '#F18F01',
        'font_color': 'white',
        'border': 1,
        'num_format': '#,##0.00'
    })
    
    # Obtener datos adicionales para el análisis
    ventas_periodo = Venta.objects.filter(fecha__range=(fecha_inicio, fecha_fin))
    total_ventas_periodo = ventas_periodo.count()
    total_valor_periodo = ventas_periodo.aggregate(total=Sum('total'))['total'] or 0
    ventas_fiado = ventas_periodo.filter(es_fiado=True).count()
    valor_fiado = ventas_periodo.filter(es_fiado=True).aggregate(total=Sum('total'))['total'] or 0
    
    # ===== HOJA 1: RESUMEN EJECUTIVO =====
    worksheet_resumen = workbook.add_worksheet('Resumen Ejecutivo')
    worksheet_resumen.set_column('A:A', 35)
    worksheet_resumen.set_column('B:B', 25)
    
    worksheet_resumen.merge_range('A1:B1', 'RESUMEN EJECUTIVO DE CLIENTES - TRADE INVENTORY', header_format)
    worksheet_resumen.merge_range('A2:B2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    worksheet_resumen.merge_range('A3:B3', f'Reporte generado el: {timezone.now().replace(tzinfo=None).strftime("%d/%m/%Y %H:%M")}', subheader_format)
    
    # Calcular métricas de clientes
    total_clientes = len(clientes_top)
    total_compras = sum(cliente['total_compras'] for cliente in clientes_top)
    total_gastado = sum(float(cliente['total_gastado']) for cliente in clientes_top)
    promedio_compra_general = total_gastado / total_compras if total_compras > 0 else 0
    
    # Segmentación de clientes
    clientes_alto_valor = sum(1 for cliente in clientes_top if float(cliente['promedio_compra']) > 100)
    clientes_medio_valor = sum(1 for cliente in clientes_top if 50 < float(cliente['promedio_compra']) <= 100)
    clientes_bajo_valor = sum(1 for cliente in clientes_top if float(cliente['promedio_compra']) <= 50)
    
    resumen_data = [
        ['MÉTRICAS GENERALES', ''],
        ['Total de Clientes Activos', total_clientes],
        ['Total de Compras', total_compras],
        ['Valor Total de Compras', total_gastado],
        ['Promedio por Compra', promedio_compra_general],
        ['', ''],
        ['SEGMENTACIÓN DE CLIENTES', ''],
        ['Clientes de Alto Valor (>$100)', clientes_alto_valor],
        ['Clientes de Medio Valor ($50-$100)', clientes_medio_valor],
        ['Clientes de Bajo Valor (<$50)', clientes_bajo_valor],
        ['Porcentaje Alto Valor', f"{(clientes_alto_valor/total_clientes*100):.1f}%" if total_clientes > 0 else "0%"],
        ['', ''],
        ['ANÁLISIS DE VENTAS', ''],
        ['Total Ventas en Período', total_ventas_periodo],
        ['Ventas a Fiado', ventas_fiado],
        ['Valor Ventas a Fiado', valor_fiado],
        ['Porcentaje Ventas Fiado', f"{(ventas_fiado/total_ventas_periodo*100):.1f}%" if total_ventas_periodo > 0 else "0%"],
        ['', ''],
        ['PERÍODO DE ANÁLISIS', ''],
        ['Días del Período', (fecha_fin - fecha_inicio).days + 1],
        ['Promedio Compras por Día', f"{total_compras/((fecha_fin - fecha_inicio).days + 1):.1f}" if (fecha_fin - fecha_inicio).days > 0 else "0"],
        ['Promedio Valor por Día', f"{total_gastado/((fecha_fin - fecha_inicio).days + 1):.2f}" if (fecha_fin - fecha_inicio).days > 0 else "0"],
    ]
    
    row = 4
    for metrica, valor in resumen_data:
        if metrica == '':
            row += 1
            continue
        if metrica in ['MÉTRICAS GENERALES', 'SEGMENTACIÓN DE CLIENTES', 'ANÁLISIS DE VENTAS', 'PERÍODO DE ANÁLISIS']:
            worksheet_resumen.write(row, 0, metrica, subheader_format)
            worksheet_resumen.write(row, 1, valor, subheader_format)
        else:
            worksheet_resumen.write(row, 0, metrica)
            if isinstance(valor, (int, float)) and metrica in ['Valor Total de Compras', 'Promedio por Compra', 'Valor Ventas a Fiado', 'Promedio Valor por Día']:
                worksheet_resumen.write(row, 1, float(valor), number_format)
            else:
                worksheet_resumen.write(row, 1, valor)
        row += 1
    
    # ===== HOJA 2: CLIENTES TOP =====
    if clientes_top:
        worksheet_clientes = workbook.add_worksheet('Clientes Top')
        worksheet_clientes.set_column('A:A', 10)
        worksheet_clientes.set_column('B:B', 25)
        worksheet_clientes.set_column('C:C', 15)
        worksheet_clientes.set_column('D:D', 15)
        worksheet_clientes.set_column('E:E', 20)
        worksheet_clientes.set_column('F:F', 20)
        worksheet_clientes.set_column('G:G', 15)
        worksheet_clientes.set_column('H:H', 20)
        
        worksheet_clientes.merge_range('A1:H1', 'CLIENTES CON MÁS COMPRAS - ANÁLISIS DE RENDIMIENTO', header_format)
        worksheet_clientes.merge_range('A2:H2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['Ranking', 'Cliente', 'Documento', 'Total Compras', 'Total Gastado', 'Promedio por Compra', 'Segmento', 'Porcentaje del Total']
        for col, header in enumerate(headers):
            worksheet_clientes.write(3, col, header, header_format)
        
        total_compras_analisis = 0
        total_gastado_analisis = 0
        
        for cliente in clientes_top:
            total_compras_analisis += cliente['total_compras']
            total_gastado_analisis += float(cliente['total_gastado'])
        
        row = 4
        for i, cliente in enumerate(clientes_top, 1):
            promedio = float(cliente['promedio_compra'])
            porcentaje = (float(cliente['total_gastado']) / total_gastado_analisis * 100) if total_gastado_analisis > 0 else 0
            
            # Determinar segmento
            if promedio > 100:
                segmento = "Alto Valor"
            elif promedio > 50:
                segmento = "Medio Valor"
            else:
                segmento = "Bajo Valor"
            
            worksheet_clientes.write(row, 0, f"#{i}")
            worksheet_clientes.write(row, 1, cliente['cliente__nombre'])
            worksheet_clientes.write(row, 2, cliente['cliente__documento'])
            worksheet_clientes.write(row, 3, cliente['total_compras'])
            worksheet_clientes.write(row, 4, float(cliente['total_gastado']), number_format)
            worksheet_clientes.write(row, 5, promedio, number_format)
            worksheet_clientes.write(row, 6, segmento)
            worksheet_clientes.write(row, 7, f"{porcentaje:.1f}%")
            row += 1
        
        # Totales
        worksheet_clientes.write(row, 0, "TOTALES", total_format)
        worksheet_clientes.write(row, 1, f"{len(clientes_top)} clientes", total_format)
        worksheet_clientes.write(row, 3, total_compras_analisis, total_format)
        worksheet_clientes.write(row, 4, float(total_gastado_analisis), total_format)
        worksheet_clientes.write(row, 5, f"Promedio: ${total_gastado_analisis/total_compras_analisis:.2f}" if total_compras_analisis > 0 else "N/A", total_format)
        worksheet_clientes.write(row, 7, "100.0%", total_format)
    
    # ===== HOJA 3: SEGMENTACIÓN DE CLIENTES =====
    if clientes_top:
        worksheet_segmentacion = workbook.add_worksheet('Segmentación')
        worksheet_segmentacion.set_column('A:A', 20)
        worksheet_segmentacion.set_column('B:B', 15)
        worksheet_segmentacion.set_column('C:C', 20)
        worksheet_segmentacion.set_column('D:D', 20)
        worksheet_segmentacion.set_column('E:E', 20)
        
        worksheet_segmentacion.merge_range('A1:E1', 'SEGMENTACIÓN DE CLIENTES POR VALOR', header_format)
        worksheet_segmentacion.merge_range('A2:E2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['Segmento', 'Cantidad Clientes', 'Total Gastado', 'Promedio por Cliente', 'Porcentaje']
        for col, header in enumerate(headers):
            worksheet_segmentacion.write(3, col, header, header_format)
        
        # Calcular datos por segmento
        segmentos = {
            'Alto Valor (>$100)': {'clientes': [], 'total': 0, 'cantidad': 0},
            'Medio Valor ($50-$100)': {'clientes': [], 'total': 0, 'cantidad': 0},
            'Bajo Valor (<$50)': {'clientes': [], 'total': 0, 'cantidad': 0}
        }
        
        for cliente in clientes_top:
            promedio = float(cliente['promedio_compra'])
            if promedio > 100:
                segmentos['Alto Valor (>$100)']['clientes'].append(cliente)
                segmentos['Alto Valor (>$100)']['total'] += float(cliente['total_gastado'])
                segmentos['Alto Valor (>$100)']['cantidad'] += 1
            elif promedio > 50:
                segmentos['Medio Valor ($50-$100)']['clientes'].append(cliente)
                segmentos['Medio Valor ($50-$100)']['total'] += float(cliente['total_gastado'])
                segmentos['Medio Valor ($50-$100)']['cantidad'] += 1
            else:
                segmentos['Bajo Valor (<$50)']['clientes'].append(cliente)
                segmentos['Bajo Valor (<$50)']['total'] += float(cliente['total_gastado'])
                segmentos['Bajo Valor (<$50)']['cantidad'] += 1
        
        row = 4
        for segmento, datos in segmentos.items():
            if datos['cantidad'] > 0:
                promedio_cliente = datos['total'] / datos['cantidad']
                porcentaje = (datos['cantidad'] / total_clientes * 100) if total_clientes > 0 else 0
                
                worksheet_segmentacion.write(row, 0, segmento)
                worksheet_segmentacion.write(row, 1, datos['cantidad'])
                worksheet_segmentacion.write(row, 2, float(datos['total']), number_format)
                worksheet_segmentacion.write(row, 3, float(promedio_cliente), number_format)
                worksheet_segmentacion.write(row, 4, f"{porcentaje:.1f}%")
                row += 1
        
        # Totales
        worksheet_segmentacion.write(row, 0, "TOTALES", total_format)
        worksheet_segmentacion.write(row, 1, total_clientes, total_format)
        worksheet_segmentacion.write(row, 2, float(total_gastado), total_format)
        worksheet_segmentacion.write(row, 3, f"Promedio: ${total_gastado/total_clientes:.2f}" if total_clientes > 0 else "N/A", total_format)
        worksheet_segmentacion.write(row, 4, "100.0%", total_format)
    
    # ===== HOJA 4: DETALLE DE CLIENTES =====
    # Obtener todos los clientes con sus ventas
    clientes_detallados = Cliente.objects.filter(
        venta__fecha__range=(fecha_inicio, fecha_fin)
    ).distinct().prefetch_related('venta_set').order_by('-venta__total')
    
    if clientes_detallados:
        worksheet_detalle = workbook.add_worksheet('Detalle de Clientes')
        worksheet_detalle.set_column('A:A', 10)
        worksheet_detalle.set_column('B:B', 25)
        worksheet_detalle.set_column('C:C', 15)
        worksheet_detalle.set_column('D:D', 15)
        worksheet_detalle.set_column('E:E', 20)
        worksheet_detalle.set_column('F:F', 15)
        worksheet_detalle.set_column('G:G', 20)
        
        worksheet_detalle.merge_range('A1:G1', 'DETALLE COMPLETO DE CLIENTES', header_format)
        worksheet_detalle.merge_range('A2:G2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
        
        headers = ['ID Cliente', 'Nombre', 'Documento', 'Total Compras', 'Total Gastado', 'Última Compra', 'Estado']
        for col, header in enumerate(headers):
            worksheet_detalle.write(3, col, header, header_format)
        
        row = 4
        for cliente in clientes_detallados:
            ventas_cliente = cliente.venta_set.filter(fecha__range=(fecha_inicio, fecha_fin))
            total_compras = ventas_cliente.count()
            total_gastado = ventas_cliente.aggregate(total=Sum('total'))['total'] or 0
            ultima_compra = ventas_cliente.order_by('-fecha').first()
            
            worksheet_detalle.write(row, 0, cliente.id)
            worksheet_detalle.write(row, 1, cliente.nombre)
            worksheet_detalle.write(row, 2, cliente.documento)
            worksheet_detalle.write(row, 3, total_compras)
            worksheet_detalle.write(row, 4, float(total_gastado), number_format)
            worksheet_detalle.write(row, 5, ultima_compra.fecha.replace(tzinfo=None) if ultima_compra else "N/A", date_format)
            worksheet_detalle.write(row, 6, "Activo" if total_compras > 0 else "Inactivo")
            row += 1
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_clientes_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    return response

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
    
    # Formato para totales
    total_format = workbook.add_format({
        'bold': True,
        'bg_color': '#F18F01',
        'font_color': 'white',
        'border': 1,
        'num_format': '#,##0.00'
    })
    
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

def exportar_reporte_fiados_excel(request, fiados_pendientes, clientes_fiados, fiados_antiguedad, fecha_inicio, fecha_fin):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
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
    
    # Formato para fechas
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # Formato para totales
    total_format = workbook.add_format({
        'bold': True,
        'bg_color': '#F18F01',
        'font_color': 'white',
        'border': 1,
        'num_format': '#,##0.00'
    })
    
    # ===== HOJA 1: FIADOS PENDIENTES =====
    worksheet_fiados = workbook.add_worksheet('Fiados Pendientes')
    worksheet_fiados.set_column('A:A', 25)
    worksheet_fiados.set_column('B:B', 15)
    worksheet_fiados.set_column('C:C', 15)
    worksheet_fiados.set_column('D:D', 15)
    worksheet_fiados.set_column('E:E', 15)
    
    worksheet_fiados.merge_range('A1:E1', 'FIADOS PENDIENTES', header_format)
    worksheet_fiados.merge_range('A2:E2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Cliente', 'Documento', 'Total Fiados', 'Monto Total', 'Promedio Fiado']
    for col, header in enumerate(headers):
        worksheet_fiados.write(3, col, header, header_format)
    
    row = 4
    for cliente in fiados_pendientes:
        worksheet_fiados.write(row, 0, cliente.cliente.nombre)
        worksheet_fiados.write(row, 1, cliente.cliente.documento)
        worksheet_fiados.write(row, 2, cliente.total_fiados)
        worksheet_fiados.write(row, 3, float(cliente.monto_total), number_format)
        worksheet_fiados.write(row, 4, float(cliente.promedio_fiado), number_format)
        row += 1
    
    # ===== HOJA 2: ANÁLISIS DE FIADOS =====
    worksheet_analisis = workbook.add_worksheet('Análisis de Fiados')
    worksheet_analisis.set_column('A:A', 25)
    worksheet_analisis.set_column('B:B', 15)
    worksheet_analisis.set_column('C:C', 15)
    worksheet_analisis.set_column('D:D', 15)
    worksheet_analisis.set_column('E:E', 15)
    
    worksheet_analisis.merge_range('A1:E1', 'ANÁLISIS DE FIADOS', header_format)
    worksheet_analisis.merge_range('A2:E2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Cliente', 'Dias Antiguedad', 'Fiados Antiguos', 'Fiados Recientes', 'Monto Antiguo', 'Monto Reciente']
    for col, header in enumerate(headers):
        worksheet_analisis.write(3, col, header, header_format)
    
    row = 4
    for cliente in fiados_antiguedad:
        worksheet_analisis.write(row, 0, cliente.cliente.nombre)
        worksheet_analisis.write(row, 1, cliente.dias_antiguedad.days)
        worksheet_analisis.write(row, 2, cliente.fiados_antiguos)
        worksheet_analisis.write(row, 3, cliente.fiados_recientes)
        worksheet_analisis.write(row, 4, float(cliente.monto_antiguo), number_format)
        worksheet_analisis.write(row, 5, float(cliente.monto_reciente), number_format)
        row += 1
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_fiados_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    return response

def exportar_reporte_categorias_excel(request, categorias_ventas, productos_por_categoria, categorias_margen, rotacion_categorias, fecha_inicio, fecha_fin):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
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
    
    # Formato para fechas
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    
    # Formato para totales
    total_format = workbook.add_format({
        'bold': True,
        'bg_color': '#F18F01',
        'font_color': 'white',
        'border': 1,
        'num_format': '#,##0.00'
    })
    
    # ===== HOJA 1: ANÁLISIS DE CATEGORÍAS POR VENTAS =====
    worksheet_ventas = workbook.add_worksheet('Categorías por Ventas')
    worksheet_ventas.set_column('A:A', 25)
    worksheet_ventas.set_column('B:B', 15)
    worksheet_ventas.set_column('C:C', 15)
    worksheet_ventas.set_column('D:D', 15)
    worksheet_ventas.set_column('E:E', 15)
    worksheet_ventas.set_column('F:F', 15)
    worksheet_ventas.set_column('G:G', 15)
    
    worksheet_ventas.merge_range('A1:G1', 'ANÁLISIS DE CATEGORÍAS POR VENTAS', header_format)
    worksheet_ventas.merge_range('A2:G2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Categoría', 'ID', 'Total Productos', 'Total Vendido', 'Total Ingresos', 'Costo Total', 'Margen de Ganancia']
    for col, header in enumerate(headers):
        worksheet_ventas.write(3, col, header, header_format)
    
    row = 4
    for categoria in categorias_ventas:
        worksheet_ventas.write(row, 0, categoria['producto__categoria__nombre'])
        worksheet_ventas.write(row, 1, categoria['producto__categoria__id'])
        worksheet_ventas.write(row, 2, categoria['total_productos'])
        worksheet_ventas.write(row, 3, categoria['total_vendido'])
        worksheet_ventas.write(row, 4, float(categoria['total_ingresos']), number_format)
        worksheet_ventas.write(row, 5, float(categoria['costo_total']), number_format)
        worksheet_ventas.write(row, 6, float(categoria['margen_ganancia']), number_format)
        row += 1
    
    # ===== HOJA 2: PRODUCTOS POR CATEGORÍA =====
    worksheet_productos = workbook.add_worksheet('Productos por Categoría')
    worksheet_productos.set_column('A:A', 25)
    worksheet_productos.set_column('B:B', 15)
    worksheet_productos.set_column('C:C', 15)
    worksheet_productos.set_column('D:D', 15)
    worksheet_productos.set_column('E:E', 15)
    
    worksheet_productos.merge_range('A1:E1', 'PRODUCTOS POR CATEGORÍA', header_format)
    worksheet_productos.merge_range('A2:E2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Categoría', 'Cantidad Productos', 'Stock Total', 'Valor Inventario', 'Productos Bajo Stock']
    for col, header in enumerate(headers):
        worksheet_productos.write(3, col, header, header_format)
    
    row = 4
    for categoria in productos_por_categoria:
        worksheet_productos.write(row, 0, categoria['categoria__nombre'])
        worksheet_productos.write(row, 1, categoria['cantidad_productos'])
        worksheet_productos.write(row, 2, float(categoria['stock_total']), number_format)
        worksheet_productos.write(row, 3, float(categoria['valor_inventario']), number_format)
        worksheet_productos.write(row, 4, categoria['productos_bajo_stock'])
        row += 1
    
    # ===== HOJA 3: CATEGORÍAS CON MEJOR MARGEN =====
    worksheet_margen = workbook.add_worksheet('Categorías con Mejor Margen')
    worksheet_margen.set_column('A:A', 25)
    worksheet_margen.set_column('B:B', 15)
    
    worksheet_margen.merge_range('A1:B1', 'CATEGORÍAS CON MEJOR MARGEN', header_format)
    worksheet_margen.merge_range('A2:B2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Categoría', 'Margen Promedio']
    for col, header in enumerate(headers):
        worksheet_margen.write(3, col, header, header_format)
    
    row = 4
    for categoria in categorias_margen:
        worksheet_margen.write(row, 0, categoria['producto__categoria__nombre'])
        worksheet_margen.write(row, 1, float(categoria['margen_promedio']), number_format)
        row += 1
    
    # ===== HOJA 4: ROTACIÓN DE INVENTARIO =====
    worksheet_rotacion = workbook.add_worksheet('Rotación de Inventario')
    worksheet_rotacion.set_column('A:A', 25)
    worksheet_rotacion.set_column('B:B', 15)
    worksheet_rotacion.set_column('C:C', 15)
    worksheet_rotacion.set_column('D:D', 15)
    
    worksheet_rotacion.merge_range('A1:D1', 'ROTACIÓN DE INVENTARIO POR CATEGORÍA', header_format)
    worksheet_rotacion.merge_range('A2:D2', f'Período: {fecha_inicio.strftime("%d/%m/%Y")} al {fecha_fin.strftime("%d/%m/%Y")}', subheader_format)
    
    headers = ['Categoría', 'Productos Vendidos', 'Unidades Vendidas', 'Valor Vendido']
    for col, header in enumerate(headers):
        worksheet_rotacion.write(3, col, header, header_format)
    
    row = 4
    for categoria in rotacion_categorias:
        worksheet_rotacion.write(row, 0, categoria['categoria__nombre'])
        worksheet_rotacion.write(row, 1, categoria['productos_vendidos'])
        worksheet_rotacion.write(row, 2, categoria['unidades_vendidas'])
        worksheet_rotacion.write(row, 3, float(categoria['valor_vendido']), number_format)
        row += 1
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_categorias_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    
    return response

@login_required
def debug_stock_proveedores(request):
    """Función de debug para verificar productos bajo stock por proveedor"""
    from productos.models import Producto
    
    # Obtener todos los productos con sus proveedores
    productos = Producto.objects.filter(
        proveedor__isnull=False
    ).select_related('proveedor').all()
    
    debug_data = {}
    
    for producto in productos:
        proveedor_nombre = producto.proveedor.nombre if producto.proveedor else 'Sin proveedor'
        
        if proveedor_nombre not in debug_data:
            debug_data[proveedor_nombre] = []
        
        # Verificar si está bajo stock
        stock_minimo = producto.stock_minimo if producto.stock_minimo is not None else 5
        bajo_stock = producto.stock_actual <= stock_minimo
        
        debug_data[proveedor_nombre].append({
            'producto': producto.nombre,
            'stock_actual': producto.stock_actual,
            'stock_minimo': producto.stock_minimo,
            'stock_minimo_efectivo': stock_minimo,
            'bajo_stock': bajo_stock,
            'sin_stock': producto.stock_actual == 0,
            'comparacion': f"{producto.stock_actual} <= {stock_minimo} = {bajo_stock}"
        })
    
    # Calcular totales por proveedor
    totales_por_proveedor = {}
    for proveedor, productos_list in debug_data.items():
        bajo_stock_count = sum(1 for p in productos_list if p['bajo_stock'])
        sin_stock_count = sum(1 for p in productos_list if p['sin_stock'])
        totales_por_proveedor[proveedor] = {
            'total_productos': len(productos_list),
            'bajo_stock': bajo_stock_count,
            'sin_stock': sin_stock_count,
            'normal': len(productos_list) - bajo_stock_count
        }
    
    context = {
        'debug_data': debug_data,
        'totales_por_proveedor': totales_por_proveedor,
        'total_proveedores': len(debug_data)
    }
    
    return render(request, 'reportes/debug_stock_proveedores.html', context)

