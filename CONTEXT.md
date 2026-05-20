# InventoryApp — Contexto del Proyecto

> Este archivo debe mantenerse actualizado por cualquier agente o desarrollador que trabaje en el proyecto.
> Registra el estado actual, tareas completadas y pendientes, decisiones tecnicas y notas relevantes.

---

## Descripcion General

Aplicacion web de gestion de inventario construida con Flask + PostgreSQL.
Permite registrar, buscar, filtrar y visualizar items de inventario con alertas de stock.

---

## Tech Stack

| Capa | Tecnologia |
|------|-----------|
| Backend | Python 3.9 / Flask 3.0.0 |
| ORM | SQLAlchemy 2.0.23 / Flask-SQLAlchemy 3.1.1 |
| Base de datos | PostgreSQL (psycopg2-binary) — SQLite para desarrollo local y tests |
| Frontend | Jinja2 + Bootstrap 5.3.2 + Bootstrap Icons |
| Servidor (prod) | Gunicorn 21.2.0 |
| Variables de entorno | python-dotenv 1.0.0 |
| Testing | pytest 8.3.4 + pytest-flask 1.3.0 |

---

## Estructura del Proyecto

```
InventoryApp/
├── app/
│   ├── __init__.py          # App factory, inicializacion DB, error handlers (404, 500, 400)
│   ├── models.py            # Modelo InventoryItem (SQLAlchemy)
│   ├── routes.py            # Todas las rutas y logica de negocio
│   └── templates/
│       ├── base.html        # Layout base con navbar y flash messages
│       ├── index.html       # Dashboard con stats, busqueda, tabla y botones CRUD
│       ├── add_item.html    # Formulario agregar item con preview en vivo
│       ├── edit_item.html   # Formulario editar item pre-poblado + modal eliminar
│       ├── item_detail.html # Vista detalle de un item
│       └── error.html       # Pagina de error para 404/500/400
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures de pytest (app, client, sample_item)
│   └── test_routes.py       # 37 tests cubriendo todas las rutas y el modelo
├── config.py                # Configuracion dev/prod/testing via variables de entorno
├── run.py                   # Entry point del servidor de desarrollo
├── requirements.txt         # Dependencias Python (incluye pytest)
└── CONTEXT.md               # Este archivo
```

---

## Modelo de Datos

### `InventoryItem` (tabla: `inventory_items`)

| Campo | Tipo | Notas |
|-------|------|-------|
| id | Integer | PK, autoincrement |
| name | String(200) | Requerido |
| description | Text | Opcional |
| quantity | Integer | Default 0, no negativo |
| price | Float | Opcional, positivo |
| category | String(100) | Opcional |
| sku | String(100) | Unico, opcional |
| created_at | DateTime | Auto |
| updated_at | DateTime | Auto, on update |

**Metodos helper:** `stock_status` (in_stock / low_stock / out_of_stock), `to_dict()`

---

## Rutas Implementadas

| Metodo | Ruta | Estado | Descripcion |
|--------|------|--------|-------------|
| GET | `/` | ✅ Completo | Dashboard con stats, busqueda, filtros, paginacion |
| GET/POST | `/add` | ✅ Completo | Logica + template funcionales. Bugs resueltos (2026-02-20) |
| GET | `/health` | ✅ Completo | Health check endpoint |
| GET | `/api/items` | ✅ Completo | API JSON de items |
| GET/POST | `/edit/<id>` | ✅ Completo | Editar item existente (2026-02-20) |
| POST | `/delete/<id>` | ✅ Completo | Eliminar item con confirmacion modal (2026-02-20) |
| GET | `/item/<id>` | ✅ Completo | Vista detalle de item (2026-02-20) |
| GET | `/export/csv` | ✅ Completo | Exportar inventario a CSV con filtro opcional (2026-02-20) |

---

## Bugs Conocidos

~~Todos los bugs criticos han sido resueltos. Ver historial de sesiones.~~

---

## Tareas Completadas

- [x] Estructura base del proyecto Flask (app factory pattern)
- [x] Modelo `InventoryItem` con todos los campos y metodos helper
- [x] Template `base.html` con navbar, flash messages y layout responsivo
- [x] Dashboard `index.html` con estadisticas, busqueda, ordenamiento, paginacion, botones CRUD
- [x] CRUD completo: rutas y templates para agregar, editar, eliminar y ver detalle de items
- [x] API JSON `/api/items` con paginacion, busqueda y metadata
- [x] Exportacion CSV `/export/csv` con filtro de busqueda opcional
- [x] Health check `/health`
- [x] Manejo de errores 404, 500, 400 con `error.html`
- [x] Configuracion dev/prod/testing con soporte a `DATABASE_URL` y credenciales individuales
- [x] Tests automatizados: 37 tests, 0 warnings, SQLite in-memory (no requiere PostgreSQL)
- [x] Validado en servidor local con SQLite — todas las rutas responden correctamente

---

## Tareas Pendientes

### Alta Prioridad (Bugs)
- [x] **Fix Bug 1:** Corregido `url_for('main.*')` → `url_for('inventory.*')` en `add_item.html` (2026-02-20)
- [x] **Fix Bug 2:** Template reescrito con HTML puro usando `form_data` dict; eliminada dependencia de Flask-WTF (2026-02-20)
- [x] **Fix Bug 3:** Corregido `{% block extra_scripts %}` → `{% block extra_js %}` en `add_item.html` — el JS del preview no se ejecutaba (2026-02-20)
- [x] Creado `app/templates/error.html` con pagina de error para 404/500/400 (2026-02-20)

### Media Prioridad
- [x] Implementar edicion de items: ruta `GET/POST /edit/<id>` + template `edit_item.html` (2026-02-20)
- [x] Implementar eliminacion de items: ruta `POST /delete/<id>` con confirmacion modal (2026-02-20)
- [x] Agregar botones de editar/eliminar en la tabla del dashboard (`index.html`) (2026-02-20)

### Baja Prioridad
- [x] Vista de detalle por item (`/item/<id>`) + `item_detail.html` (2026-02-20)
- [x] Exportar inventario a CSV — ruta `/export/csv`, respeta filtro de busqueda (2026-02-20)
- [x] Paginacion en la API JSON — soporta `?page=`, `?per_page=` (max 100), `?search=` (2026-02-20)
- [x] Tests automatizados — pytest + pytest-flask, SQLite in-memory, 30+ tests en `tests/test_routes.py` (2026-02-20)

---

## Decisiones Tecnicas

- **App factory pattern** en `__init__.py` para facilitar testing y multiples instancias
- **PostgreSQL** como base de datos de produccion; **SQLite** para desarrollo local y tests
- **Bootstrap 5** via CDN para no gestionar assets estaticos por ahora
- **`DATABASE_URL`** toma prioridad sobre credenciales individuales (estandar Heroku/Render/Railway)
- **`db.session.get()` + `abort(404)`** en lugar de `get_or_404()` para compatibilidad con SQLAlchemy 2.0
- **Tests** usan `TestingConfig` con SQLite in-memory — no requieren servidor de base de datos

---

## Como Correr el Proyecto

### Tests (no requiere PostgreSQL)
```bash
.venv/bin/pytest tests/ -v
```

### Desarrollo local con SQLite
```bash
DATABASE_URL=sqlite:///local_dev.db FLASK_ENV=development .venv/bin/python run.py
```

### Desarrollo local con PostgreSQL
```bash
# Configurar en .env o exportar:
DB_HOST=localhost DB_PORT=5432 DB_NAME=inventory_db DB_USER=... DB_PASSWORD=...
FLASK_ENV=development .venv/bin/python run.py
```

### Produccion con Gunicorn
```bash
DATABASE_URL=postgresql://... SECRET_KEY=... gunicorn -w 3 -b 0.0.0.0:8000 "run:app"
```

---

## Notas para Agentes

- El virtual environment esta en `.venv/` (Python 3.9) — dependencias instaladas
- El archivo `.venv.example/` parece ser un backup del entorno virtual, no borrarlo sin confirmar
- `config.py` tiene 4 configs: `DevelopmentConfig`, `ProductionConfig`, `TestingConfig`, seleccionadas via `FLASK_ENV`
- `run.py` llama `create_app()` sin argumento — la config se auto-detecta desde `FLASK_ENV`
- Al agregar nuevas rutas: registrarlas en la tabla de rutas y agregar tests en `tests/test_routes.py`
- Al completar tareas: moverlas de "Pendientes" a "Completadas" con la fecha
- Al iniciar sesion: leer este archivo antes de hacer cambios

---

## Historial de Sesiones

| Fecha | Agente | Acciones |
|-------|--------|----------|
| 2026-02-20 | Claude Sonnet 4.6 | Exploracion inicial del proyecto, diagnostico de estado, creacion de CONTEXT.md |
| 2026-02-20 | Claude Sonnet 4.6 | Lectura profunda de `routes.py`, `models.py`, `__init__.py`, `add_item.html`. Descubiertos 3 bugs criticos en `add_item.html` (blueprint name incorrecto + uso de Flask-WTF sin tenerlo instalado + block name incorrecto para JS). Actualizacion de CONTEXT.md con estado real. |
| 2026-02-20 | Claude Sonnet 4.6 | Resueltos los 3 bugs en `add_item.html`. Creado `error.html`. La ruta `/add` esta completamente funcional. |
| 2026-02-20 | Claude Sonnet 4.6 | Implementadas rutas `/edit/<id>` y `/delete/<id>`. Creado `edit_item.html`. Agregados botones de editar/eliminar con modal de confirmacion en `index.html`. CRUD completo. |
| 2026-02-20 | Claude Sonnet 4.6 | Completadas todas las tareas pendientes: vista detalle `/item/<id>` + `item_detail.html`, exportacion CSV `/export/csv`, paginacion y busqueda en `/api/items`, tests con pytest (37 tests, SQLite in-memory). Proyecto 100% funcional. |
| 2026-02-20 | Claude Sonnet 4.6 | Deployment de validacion: instaladas dependencias, 37/37 tests pasados sin warnings, servidor Flask levantado con SQLite, smoke test de todas las rutas exitoso. Fixes adicionales: soporte `DATABASE_URL` en `config.py`, bug en `run.py` (pasaba string en vez de config object), `get_or_404()` reemplazado por `db.session.get()` + `abort(404)` (SQLAlchemy 2.0 moderno). |
