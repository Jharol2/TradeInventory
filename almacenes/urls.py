from django.urls import path
from . import views

app_name = 'almacenes'

urlpatterns = [
    path('', views.lista_almacenes, name='lista_almacenes'),
    path('crear/', views.crear_almacen, name='crear_almacen'),
    path('editar/<int:pk>/', views.editar_almacen, name='editar_almacen'),
    path('cambiar-estado/<int:pk>/', views.cambiar_estado_almacen, name='cambiar_estado_almacen'),
] 