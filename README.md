# ERG-Inventory — Backend

API REST con **Django + Django REST Framework**.  
Base de datos: **Supabase (PostgreSQL)**.  
Deploy: **Render**.

---

## Estructura del proyecto

```
erg_inventory_backend/
├── config/               ← Configuración Django (settings, urls, wsgi)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                 ← Utilidades reutilizables
│   ├── permissions.py    ← IsAdmin, IsAdminOrReadOnly, etc.
│   ├── pagination.py
│   └── mixins.py
├── users/                ← Modelo Usuario + Auth JWT
├── productos/            ← Catálogo de productos
├── clientes/             ← Clientes
├── proveedores/          ← Proveedores
├── ventas/               ← Registro de ventas
├── compras/              ← Órdenes de compra
├── entregas/             ← Seguimiento de entregas
├── movimientos/          ← Entradas / Salidas / Ajustes de stock
├── kardex/               ← Vista de movimientos con saldo acumulado
├── reportes/             ← Resumen estadístico
├── manage.py
├── requirements.txt
├── render.yaml           ← Configuración de deploy en Render
└── .env                  ← Variables de entorno (NO subir a git)
```

---

## Instalación local

```bash
# 1. Clonar y entrar al proyecto
git clone <tu-repo>
cd erg_inventory_backend

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env .env.local
# Edita .env con tus datos de Supabase

# 5. Migrar base de datos
python manage.py migrate

# 6. Crear superusuario admin
python manage.py createsuperuser

# 7. Iniciar servidor
python manage.py runserver
```

---

## Variables de entorno (.env)

```env
SECRET_KEY=django-insecure-cambia-esta-clave-en-produccion
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Supabase — ve a Project Settings > Database > Connection string (URI)
DATABASE_URL=postgresql://postgres:TU_PASSWORD@db.TU_PROYECTO.supabase.co:5432/postgres

# Frontend URL (para CORS)
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://tu-app.vercel.app
```

---

## Endpoints de la API

### Auth
| Método | URL | Descripción |
|--------|-----|-------------|
| POST | `/api/auth/login/` | Iniciar sesión → devuelve `access` + `refresh` |
| POST | `/api/auth/refresh/` | Renovar access token |
| GET | `/api/auth/me/` | Perfil del usuario autenticado |

### Todos los módulos siguen el mismo patrón:

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/<modulo>/` | Listar (paginado, buscable) |
| POST | `/api/<modulo>/` | Crear |
| GET | `/api/<modulo>/<id>/` | Obtener uno |
| PUT | `/api/<modulo>/<id>/` | Actualizar completo |
| PATCH | `/api/<modulo>/<id>/` | Actualizar parcial |
| DELETE | `/api/<modulo>/<id>/` | Eliminar |

**Módulos:** `usuarios`, `productos`, `clientes`, `proveedores`, `ventas`, `compras`, `entregas`, `movimientos`

### Especiales
| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/kardex/` | Kardex completo con saldo acumulado |
| GET | `/api/kardex/?producto_id=3` | Kardex filtrado por producto |
| GET | `/api/kardex/productos/` | Productos con movimientos |
| GET | `/api/reportes/resumen/` | Dashboard estadístico completo |

### Búsqueda y filtros
```
GET /api/productos/?search=laptop
GET /api/ventas/?search=pendiente&ordering=-fecha
GET /api/productos/?ordering=stock
```

---

## Autenticación JWT

Todos los endpoints (excepto login) requieren el header:
```
Authorization: Bearer <access_token>
```

---

## Roles y permisos

| Rol | Permisos |
|-----|----------|
| Administrador | Todo: CRUD completo en todos los módulos |
| Vendedor | Crear/editar ventas, ver productos y clientes |
| Almacenista | Crear movimientos de stock, ver/editar productos |
| Contador | Solo lectura en ventas, compras, reportes |
| Empleado | Solo lectura general |

---

## Deploy en Render

1. Sube el proyecto a GitHub
2. En Render → **New Web Service** → conecta el repo
3. Configura las variables de entorno:
   - `SECRET_KEY` (genera uno seguro)
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `.onrender.com`
   - `DATABASE_URL` = tu URL de Supabase
   - `CORS_ALLOWED_ORIGINS` = URL de tu app en Vercel
4. Build command: `pip install -r requirements.txt && python manage.py migrate --no-input && python manage.py collectstatic --no-input`
5. Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

---

## Configurar Supabase

1. Crea un proyecto en [supabase.com](https://supabase.com)
2. Ve a **Project Settings → Database**
3. Copia la **Connection string (URI)**
4. Pégala en `DATABASE_URL` del `.env`
5. Ejecuta `python manage.py migrate` — Django crea todas las tablas automáticamente

