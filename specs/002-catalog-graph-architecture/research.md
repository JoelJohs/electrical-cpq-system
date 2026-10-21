# Research & Technical Decisions: Arquitectura Base y Catálogo en Grafo Dirigido (Fase 3)

**Feature**: `002-catalog-graph-architecture`  
**Date**: 2026-10-19  
**Status**: Completed  

---

## 1. Modelado de Compatibilidad Eléctrica: Grafo Dirigido vs. BD Espejo / Bidireccional

### Contexto
En sistemas de cotización y configuración técnica (CPQ) para tableros eléctricos y aparamenta de distribución, la relación física entre componentes posee una estricta jerarquía física:
- Un tablero (`BOARD`) aloja interruptores (`COMPONENT`).
- Un interruptor aloja accesorios (`ACCESSORY`, ej. bobinas de disparo, contactos auxiliares).
- Un tablero requiere accesorios de montaje (`ACCESSORY`, ej. kits de zapatas para neutro/tierra).

### Decisión
Adoptar un modelo relacional de **grafo dirigido en SQL** compuesto por dos tablas:
1. `Product` (Nodos): Entidad física con `sku`, `name`, `slug`, `product_type`, `specs` (JSONB) y `is_active`.
2. `ProductCompatibility` (Aristas dirigidas): Relación entre `source` (contenedor/anfitrión) y `target` (elemento a instalar/complemento), tipada con `relationship_type` (`COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`).

### Racional del rechazo a `is_bidirectional = BooleanField`
1. **Asimetría física y funcional**: Marcar `is_bidirectional = True` destruiría la semántica del negocio: al consultar los accesorios de un contacto auxiliar, el sistema devolvería incorrectamente el interruptor completo.
2. **Degradación de consultas en ORM**: Unir conjuntos directos e inversos con `.union()` anula optimizaciones de Django (`select_related`, `prefetch_related`), impidiendo la precarga eficiente de árboles de componentes y rompiendo la paginación nativa sobre QuerySets compuestos.
3. **Manejo de relaciones simétricas (`ALTERNATIVE_TO`)**: Para relaciones simétricas puntuales (sustitutos equivalentes), se utiliza una consulta disyuntiva `Q(source=p) | Q(target=p)` a nivel de servicio, manteniendo la pureza y los índices del modelo relacional.

### Alternativas Consideradas
- **Base de datos de grafos dedicada (Neo4j / Memgraph)**: Descartada por complejidad operativa y sobreingeniería en un MVP; PostgreSQL maneja millones de aristas con índices B-Tree en < 1ms.
- **Triggers y replicación en BD espejo**: Descartada por fragilidad, desincronización con el ORM de Django y dificultad de depuración.

---

## 2. Framework de API para el Catálogo: Django Ninja vs. Django REST Framework (DRF)

### Contexto
El usuario seleccionó la opción B (Framework de API dedicado) para exponer las consultas del grafo al cotizador/frontend con esquemas tipados y documentación OpenAPI interactiva.

### Decisión
Seleccionar **Django Ninja** (`django-ninja>=1.3.0`):
- Basado en type-hints nativos de Python 3.10+ y Pydantic v2.
- Genera automáticamente documentación interactiva OpenAPI / Swagger en `/api/docs`.
- Rendimiento superior a DRF gracias a validación Pydantic en C/Rust y bajo consumo de memoria.
- Sintaxis intuitiva y limpia para definir esquemas jerárquicos (árboles de compatibilidad).

### Racional
Django Ninja permite estructurar esquemas de respuesta anidados (`ProductTreeSchema`, `CompatibilityEdgeSchema`) con tipado estricto sin la sobrecarga de serializadores complejos de DRF, alineándose con Python 3.14 y la arquitectura modular del proyecto.

### Alternativas Consideradas
- **Django REST Framework (DRF)**: Robusto pero con mayor boilerplate y sobrecarga en serialización anidada de grafos.
- **Vistas Django estándar con `JsonResponse`**: Requiere serialización manual en cada vista y no genera documentación OpenAPI interactiva.

---

## 3. Estrategia de Persistencia: PostgreSQL Contenerizado (Docker) Local y VPS

### Contexto
El usuario especificó utilizar PostgreSQL contenerizado con Docker para el entorno de desarrollo local, con el objetivo de disponer de un entorno desechable, aislado y manipulable sin comprometer datos sensibles ni requerir instalación de PostgreSQL en el sistema operativo base, manteniendo paridad con el VPS de producción.

### Decisión
1. Definir un archivo `docker-compose.yml` en la raíz del proyecto para levantar PostgreSQL (imagen oficial `postgres:17-alpine`) con un volumen persistente pero fácilmente reseteable (`docker compose down -v`).
2. Configurar Django mediante `DATABASE_URL` (`django-environ`) para conectarse a `postgres://postgres:postgres@localhost:5432/electrical_cpq`.
3. Mantener el driver de alto rendimiento `psycopg[binary]>=3.3.6` (ya presente en `pyproject.toml`).
4. Proporcionar un script auxiliar `scripts/db_dev.sh` para iniciar, detener y reiniciar la base de datos local en Docker sin fricción.

### Racional
- Permite probar índices compuestos B-Tree y campos `JSONField` directamente en el motor real de producción (PostgreSQL).
- Totalmente desechable: si los datos de prueba quedan corruptos, basta con reiniciar el contenedor y volver a ejecutar `python manage.py migrate`.
- Desacoplamiento total: en el VPS se utiliza la misma variable `DATABASE_URL` apuntando a PostgreSQL nativo o en Docker.

---

## 4. Arquitectura Modular en Capas para la App `catalog`

### Contexto
El checklist de Fase 3 exige construir una estructura modular que separe dominio, servicios y capa de presentación.

### Decisión
Organizar la aplicación `catalog` en `src/catalog/` con la siguiente separación estricta de responsabilidades:
```text
src/catalog/
├── __init__.py
├── apps.py                  # Configuración de Django App
├── models.py                # Capa de Dominio: Product, ProductCompatibility, Enums, Constraints
├── selectors.py             # Capa de Consulta: Consultas de grafo optimizadas (get_compatible_tree, get_accessories)
├── services.py              # Capa de Mutación: Creación y validación de aristas y productos
├── api.py                   # Capa de Presentación: Router de Django Ninja con esquemas de entrada/salida
├── admin.py                 # Capa Administrativa: Django Admin con inlines de compatibilidad
└── tests/                   # Pruebas automatizadas unitarias, de integración y de rendimiento
```

### Racional
- **Separación de Selectores y Servicios**: Sigue el patrón estándar de Django moderno (HackSoft Django Styleguide). Los selectores solo leen (`select_related`, `prefetch_related`) sin efectos secundarios; los servicios encapsulan mutaciones y reglas de negocio.
- **Rendimiento garantizado (Sin N+1)**: El selector `get_product_compatibility_tree(sku)` utiliza una única consulta con `Prefetch` anidado, resolviendo todo el árbol del tablero en exactamente 2 consultas SQL fijas.
