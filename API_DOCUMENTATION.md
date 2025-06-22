# 📚 DOCUMENTACIÓN DE APIs REST - TRADEINVENTORY

## 🎯 **INFORMACIÓN GENERAL**

**Base URL:** `http://127.0.0.1:8000/api/`

**Autenticación:** Todas las APIs requieren autenticación de usuario (login)

**Formato de respuesta:** JSON

**Headers requeridos:**
```
Content-Type: application/json
Authorization: Session (cookies de Django)
```

---

## 📦 **MÓDULO PRODUCTOS**

### **GET /api/productos/**
**Listar todos los productos**

**Parámetros de consulta:**
- `q` (opcional): Término de búsqueda en nombre o descripción
- `categoria` (opcional): ID de categoría para filtrar
- `stock` (opcional): `bajo` (≤5) o `normal` (>5)
- `estado` (opcional): `activo`, `inactivo`, `todos`

**Ejemplo:**
```bash
GET /api/productos/?q=coca&categoria=1&stock=bajo
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Coca Cola 2L",
    "precio": 2500,
    "stock_actual": 3,
    "stock_minimo": 10,
    "categoria_nombre": "Bebidas",
    "proveedor_nombre": "Distribuidora ABC",
    "activo": true
  }
]
```

### **POST /api/productos/**
**Crear un nuevo producto**

**Body:**
```json
{
  "nombre": "Coca Cola 2L",
  "descripcion": "Bebida gaseosa",
  "precio": 2500,
  "stock_actual": 50,
  "stock_minimo": 10,
  "categoria": 1,
  "proveedor": 1
}
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Coca Cola 2L",
  "descripcion": "Bebida gaseosa",
  "precio": 2500,
  "stock_actual": 50,
  "stock_minimo": 10,
  "categoria": {
    "id": 1,
    "nombre": "Bebidas",
    "descripcion": "Bebidas y refrescos",
    "activo": true
  },
  "proveedor": {
    "id": 1,
    "nombre": "Distribuidora ABC",
    "telefono": "123456789",
    "email": "abc@example.com",
    "direccion": "Calle 123",
    "activo": true
  },
  "imagen": null,
  "activo": true,
  "fecha_creacion": "2025-01-08T10:30:00Z"
}
```

### **GET /api/productos/{id}/**
**Obtener un producto específico**

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Coca Cola 2L",
  "descripcion": "Bebida gaseosa",
  "precio": 2500,
  "stock_actual": 50,
  "stock_minimo": 10,
  "categoria": {
    "id": 1,
    "nombre": "Bebidas",
    "descripcion": "Bebidas y refrescos",
    "activo": true
  },
  "proveedor": {
    "id": 1,
    "nombre": "Distribuidora ABC",
    "telefono": "123456789",
    "email": "abc@example.com",
    "direccion": "Calle 123",
    "activo": true
  },
  "imagen": null,
  "activo": true,
  "fecha_creacion": "2025-01-08T10:30:00Z"
}
```

### **PUT /api/productos/{id}/**
**Actualizar un producto**

**Body:**
```json
{
  "nombre": "Coca Cola 2L Actualizada",
  "precio": 2800,
  "stock_actual": 45
}
```

### **DELETE /api/productos/{id}/**
**Eliminar un producto**

### **GET /api/productos/stock_bajo/**
**Obtener productos con stock bajo (≤5)**

### **POST /api/productos/{id}/cambiar_estado/**
**Cambiar estado activo/inactivo**

### **POST /api/productos/{id}/actualizar_stock/**
**Actualizar stock de un producto**

**Body:**
```json
{
  "cantidad": 100
}
```

---

## 👥 **MÓDULO CLIENTES**

### **GET /api/clientes/**
**Listar todos los clientes**

**Parámetros de consulta:**
- `q` (opcional): Término de búsqueda en nombre, apellido o email
- `estado` (opcional): `activo`, `inactivo`

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "telefono": "123456789",
    "email": "juan@example.com",
    "activo": true
  }
]
```

### **POST /api/clientes/**
**Crear un nuevo cliente**

**Body:**
```json
{
  "nombre": "Juan",
  "apellido": "Pérez",
  "telefono": "123456789",
  "email": "juan@example.com",
  "direccion": "Calle 123",
  "documento": "12345678"
}
```

### **GET /api/clientes/{id}/**
**Obtener un cliente específico**

### **PUT /api/clientes/{id}/**
**Actualizar un cliente**

### **DELETE /api/clientes/{id}/**
**Eliminar un cliente**

### **GET /api/clientes/{id}/fiados/**
**Obtener fiados de un cliente**

### **POST /api/clientes/{id}/cambiar_estado/**
**Cambiar estado activo/inactivo**

---

## 💳 **MÓDULO FIADOS**

### **GET /api/fiados/**
**Listar todos los fiados**

**Parámetros de consulta:**
- `cliente` (opcional): ID del cliente
- `estado` (opcional): Estado del fiado

### **POST /api/fiados/**
**Crear un nuevo fiado**

### **GET /api/fiados/{id}/**
**Obtener un fiado específico**

### **PUT /api/fiados/{id}/**
**Actualizar un fiado**

### **DELETE /api/fiados/{id}/**
**Eliminar un fiado**

### **POST /api/fiados/{id}/abonar/**
**Abonar a un fiado**

**Body:**
```json
{
  "monto": 5000
}
```

---

## 🛒 **MÓDULO VENTAS**

### **GET /api/ventas/**
**Listar todas las ventas**

**Parámetros de consulta:**
- `cliente` (opcional): ID del cliente
- `es_fiado` (opcional): `true` o `false`
- `estado` (opcional): Estado de la venta
- `fecha` (opcional): Fecha específica (YYYY-MM-DD)

**Respuesta:**
```json
[
  {
    "id": 1,
    "cliente_nombre": "Juan Pérez",
    "fecha": "2025-01-08T10:30:00Z",
    "total": 5000,
    "es_fiado": false,
    "monto_abonado": 0,
    "estado": "completada"
  }
]
```

### **POST /api/ventas/**
**Crear una nueva venta**

**Body:**
```json
{
  "cliente_id": 1,
  "es_fiado": false,
  "detalles": [
    {
      "producto_id": 1,
      "cantidad": 2
    },
    {
      "producto_id": 2,
      "cantidad": 1
    }
  ]
}
```

### **GET /api/ventas/{id}/**
**Obtener una venta específica**

### **PUT /api/ventas/{id}/**
**Actualizar una venta**

### **DELETE /api/ventas/{id}/**
**Eliminar una venta**

### **GET /api/ventas/ventas_hoy/**
**Obtener ventas del día actual**

**Respuesta:**
```json
{
  "ventas": [...],
  "total_hoy": 15000,
  "fecha": "2025-01-08"
}
```

### **GET /api/ventas/estadisticas/**
**Obtener estadísticas de ventas**

**Respuesta:**
```json
{
  "total_hoy": 15000,
  "ventas_hoy": 5,
  "ventas_normales_hoy": 3,
  "ventas_fiado_hoy": 2,
  "total_general": 50000
}
```

### **POST /api/ventas/{id}/abonar/**
**Abonar a una venta a fiado**

**Body:**
```json
{
  "monto": 2500
}
```

---

## 📋 **MÓDULO DETALLES DE VENTA**

### **GET /api/detalles-venta/**
**Listar todos los detalles de venta**

**Parámetros de consulta:**
- `venta` (opcional): ID de la venta
- `producto` (opcional): ID del producto

### **GET /api/detalles-venta/{id}/**
**Obtener un detalle específico**

---

## 🧪 **CASOS DE PRUEBA PARA POSTMAN**

### **1. Listar Productos**
```
GET http://127.0.0.1:8000/api/productos/
```

### **2. Crear Producto**
```
POST http://127.0.0.1:8000/api/productos/
Content-Type: application/json

{
  "nombre": "Coca Cola 2L",
  "descripcion": "Bebida gaseosa",
  "precio": 2500,
  "stock_actual": 50,
  "stock_minimo": 10,
  "categoria": 1,
  "proveedor": 1
}
```

### **3. Buscar Productos**
```
GET http://127.0.0.1:8000/api/productos/?q=coca&stock=bajo
```

### **4. Actualizar Producto**
```
PUT http://127.0.0.1:8000/api/productos/1/
Content-Type: application/json

{
  "precio": 2800,
  "stock_actual": 45
}
```

### **5. Eliminar Producto**
```
DELETE http://127.0.0.1:8000/api/productos/1/
```

### **6. Crear Cliente**
```
POST http://127.0.0.1:8000/api/clientes/
Content-Type: application/json

{
  "nombre": "Juan",
  "apellido": "Pérez",
  "telefono": "123456789",
  "email": "juan@example.com",
  "direccion": "Calle 123",
  "documento": "12345678"
}
```

### **7. Crear Venta**
```
POST http://127.0.0.1:8000/api/ventas/
Content-Type: application/json

{
  "cliente_id": 1,
  "es_fiado": false,
  "detalles": [
    {
      "producto_id": 1,
      "cantidad": 2
    }
  ]
}
```

### **8. Obtener Estadísticas**
```
GET http://127.0.0.1:8000/api/ventas/estadisticas/
```

---

## ⚠️ **NOTAS IMPORTANTES**

1. **Autenticación:** Todas las APIs requieren estar logueado en Django
2. **CSRF:** Las APIs REST no requieren CSRF token
3. **Formato:** Todas las respuestas son en formato JSON
4. **Códigos de estado:** 
   - 200: Éxito
   - 201: Creado
   - 400: Error de validación
   - 401: No autenticado
   - 404: No encontrado
   - 500: Error del servidor

---

## 🚀 **PRÓXIMOS PASOS**

1. **Instalar Postman** si no lo tienes
2. **Crear una colección** en Postman
3. **Configurar variables** de entorno
4. **Ejecutar las pruebas** de cada endpoint
5. **Documentar resultados** con capturas de pantalla 