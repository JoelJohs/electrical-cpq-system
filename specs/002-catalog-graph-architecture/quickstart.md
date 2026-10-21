# Quickstart: Guía de Validación y Ejecución del Catálogo Eléctrico (Fase 3)

**Feature**: `002-catalog-graph-architecture`  
**Objetivo**: Validar el modelo de datos del grafo dirigido, las restricciones de integridad relacional, las consultas optimizadas sin N+1 y la exposición API.

---

## 1. Prerrequisitos

1. **Python 3.14 con `uv`**:
   ```bash
   uv --version
   ```
2. **PostgreSQL en Docker (Entorno Desechable)**:
   ```bash
   # Iniciar el contenedor de PostgreSQL local
   docker compose up -d db
   
   # O si trabajas sin Docker momentáneamente:
   # SQLite opera de forma nativa e idéntica mediante el ORM de Django
   ```

---

## 2. Configuración y Migraciones

```bash
# 1. Configurar DATABASE_URL en .env (para PostgreSQL local):
# DATABASE_URL="postgres://postgres:postgres_dev_password@localhost:5432/electrical_cpq"

# 2. Generar y aplicar migraciones de la app 'catalog'
uv run python manage.py makemigrations catalog
uv run python manage.py migrate
```

---

## 3. Escenarios de Validación Paso a Paso

### Escenario 1: Carga de Datos Semilla Eléctricos Reales
Poblar la base de datos con un tablero, interruptores y accesorios representativos:

```bash
uv run python manage.py seed_electrical_catalog
```
**Datos creados**:
- `TAB-NQ-225` (Tablero Alumbrado NQ 225A 30 Polos, tipo `BOARD`).
- `INT-QO-120` (Interruptor QO 1P 20A, tipo `COMPONENT`).
- `INT-EDB-3100` (Interruptor EDB 3P 100A, tipo `COMPONENT`).
- `ACC-AUX-QO` (Contacto Auxiliar 1NA/1NC, tipo `ACCESSORY`).
- `KIT-ZAP-225` (Kit Zapata Neutro 225A, tipo `ACCESSORY`).

Compatibilidades dirigidas:
- `TAB-NQ-225` ──[COMPATIBLE_WITH]──▶ `INT-QO-120`
- `TAB-NQ-225` ──[COMPLEMENT_OF]──▶ `KIT-ZAP-225`
- `INT-QO-120` ──[COMPLEMENT_OF]──▶ `ACC-AUX-QO`

---

### Escenario 2: Validación de Integridad y Restricciones de Base de Datos

Comprobar que el sistema rechaza violaciones lógicas:

```python
# En consola de Django (uv run python manage.py shell):
from catalog.models import Product, ProductCompatibility, RelationshipType
from django.db import IntegrityError
from django.core.exceptions import ValidationError

tablero = Product.objects.get(sku="TAB-NQ-225")

# Test 1: Auto-relación (un producto consigo mismo) -> DEBE FALLAR
try:
    ProductCompatibility.objects.create(
        source=tablero,
        target=tablero,
        relationship_type=RelationshipType.COMPATIBLE_WITH,
    )
    print("ERROR: Permitió auto-relación")
except (IntegrityError, ValidationError):
    print("✓ PASS: Auto-relación prevenida correctamente por CheckConstraint")

# Test 2: Duplicado idéntico -> DEBE FALLAR
interruptor = Product.objects.get(sku="INT-QO-120")
try:
    ProductCompatibility.objects.create(
        source=tablero,
        target=interruptor,
        relationship_type=RelationshipType.COMPATIBLE_WITH,
    )
    print("ERROR: Permitió arista duplicada")
except IntegrityError:
    print("✓ PASS: Arista duplicada prevenida correctamente por UniqueConstraint")
```

---

### Escenario 3: Consulta del Árbol de Cotización sin N+1 Queries

Verificar que la jerarquía completa se obtiene en exactamente **2 consultas SQL**:

```python
from django.db import connection, reset_queries
from catalog.selectors import get_product_compatibility_tree

reset_queries()
tree = get_product_compatibility_tree("TAB-NQ-225")

print(f"Producto: {tree['name']} ({tree['sku']})")
print(f"Componentes compatibles: {len(tree['compatible_components'])}")
print(f"Consultas SQL ejecutadas: {len(connection.queries)}")
# Esperado: len(connection.queries) <= 2
```

---

### Escenario 4: Consulta de la API REST y Documentación Interactiva

1. Levantar servidor local:
   ```bash
   uv run python manage.py runserver
   ```
2. Acceder a la documentación Swagger interactiva:
   Abrir en navegador: `http://127.0.0.1:8000/api/docs`
3. Probar endpoint de compatibilidad vía `curl`:
   ```bash
   curl -s http://127.0.0.1:8000/api/v1/catalog/products/TAB-NQ-225/tree/ | jq .
   ```

---

### Escenario 5: Ejecución de la Suite de Pruebas Automatizadas

```bash
uv run python manage.py test catalog.tests
uv run ruff check .
```
**Resultado esperado**:
- Todas las pruebas de modelos, restricciones, selectores y API completan en verde con código de salida 0.
