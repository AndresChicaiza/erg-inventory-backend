# ERG-Inventory — Backend

API REST robusta con **Django + Django REST Framework** para la gestión integral de inventarios, nómina, facturación y finanzas.

Base de datos: **Supabase (PostgreSQL)**.  
Deploy: **Render**.

---

## 🚀 Módulos Principales

- **Facturación:** Emisión de facturas con cálculo de impuestos (IVA, Retefuente, ReteICA), anulación y estados de pago.
- **Inventario Multi-bodega:** Control de stock por ubicación, lotes y fechas de vencimiento.
- **Logística:** Gestión de despachos de ventas y **Remisiones de Traslado** entre bodegas con proceso de dos pasos (Despacho ➡️ Recepción).
- **Finanzas (CXC / CXP):** Control automático de cuentas por cobrar (clientes) y pagar (proveedores).
- **Nómina:** Gestión de empleados, períodos de nómina y liquidaciones.
- **Producción:** Órdenes de fabricación y gestión de recetas (BOM).

---

## 📂 Estructura del proyecto

```
erg_inventory_backend/
├── config/               ← Configuración Django
├── core/                 ← Mixins, Permisos (RBAC) y Utilidades
├── users/                ← Usuarios y Sedes
├── productos/            ← Catálogo y Lotes
├── bodegas/              ← Ubicaciones y Stock por bodega
├── facturacion/          ← Facturas e Impuestos
├── clientes/             ← Gestión de Clientes
├── proveedores/          ← Gestión de Proveedores
├── compras/              ← Órdenes de Compra
├── entregas/             ← Logística (Ventas y Traslados)
├── movimientos/          ← Logs de Entradas / Salidas
├── nomina/               ← RRHH y Pagos
├── cxc / cxp/            ← Cartera y Cuentas por Pagar
├── reportes/             ← Dashboard y Alertas
└── configuracion/        ← Datos de Empresa y Tarifas
```

---

## 🔐 Roles y Permisos (RBAC)

El sistema implementa un control de acceso estricto basado en roles:

| Rol | Alcance Principal |
|-----|-------------------|
| **Administrador** | Acceso total a todos los módulos y configuraciones. |
| **Contador** | Finanzas, Facturación (Lectura), Reportes y Nómina. |
| **Vendedor** | Facturación, Clientes y Consulta de Stock. |
| **Jefe de Fábrica** | Producción, Inventario y Traslados. |
| **Bodeguero** | Movimientos de Stock y Recepción de Traslados/Compras. |
| **Logística** | Gestión de Entregas y Remisiones de Traslado. |

---

## 🛠️ Instalación local

1. **Entorno Virtual:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuración:**
   Crea un archivo `.env` basado en los datos de tu base de datos:
   ```env
   DATABASE_URL=postgresql://usuario:pass@host:5432/dbname
   SECRET_KEY=tu_clave_secreta
   DEBUG=True
   ```

3. **Base de Datos:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

---

## 📈 Dashboard y Reportes

- **Resumen General:** `/api/reportes/resumen/` (Kpis financieros y de stock).
- **Alertas Críticas:** `/api/reportes/alertas/` (Vencimientos, stock bajo, cartera vencida).
- **Kardex:** `/api/kardex/` (Trazabilidad completa de productos).

---

## 📑 Documentación de API

El sistema utiliza **SimpleJWT** para autenticación. Todos los módulos exponen un CRUD estándar siguiendo las convenciones de REST.

---

© 2026 ERG Inventory - Powered by Volcano Asadores / Suministros Dacar SAS.
