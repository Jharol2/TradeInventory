from django.contrib import admin
from .models import Cliente, Fiado

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'telefono', 'email')
    list_editable = ('activo',)
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

@admin.register(Fiado)
class FiadoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'fecha', 'monto', 'pagado', 'fecha_pago')
    list_filter = ('pagado', 'fecha')
    search_fields = ('cliente__nombre',)
    readonly_fields = ('fecha', 'fecha_pago')
