from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock_actual', 'activo')
    list_filter = ('activo', 'categoria')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('precio', 'stock_actual', 'activo')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
