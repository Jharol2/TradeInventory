from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'),
    path('nueva/', views.nueva_venta, name='nueva_venta'),
    path('detalle/<int:pk>/', views.detalle_venta, name='detalle_venta'),
    path('historial/', views.historial_ventas, name='historial_ventas'),
] 