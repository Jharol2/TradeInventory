from django.contrib import admin
from .models import Almacen

@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'direccion')
    list_editable = ('activo',)
    readonly_fields = ('fecha_creacion',)
