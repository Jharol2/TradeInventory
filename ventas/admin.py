from django.contrib import admin
from .models import Venta, DetalleVenta

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha', 'cliente', 'total', 'es_fiado')
    list_filter = ('es_fiado', 'fecha', 'cliente')
    search_fields = ('cliente__nombre', 'id')
    readonly_fields = ('fecha', 'total')
    inlines = [DetalleVentaInline]

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('venta__fecha', 'producto')
    search_fields = ('venta__id', 'producto__nombre')
