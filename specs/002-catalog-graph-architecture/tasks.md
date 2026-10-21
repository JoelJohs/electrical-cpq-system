# Tasks: Arquitectura Base y Catálogo en Grafo Dirigido (Fase 3)

**Feature**: `002-catalog-graph-architecture`  
**Input**: Plan from `specs/002-catalog-graph-architecture/plan.md`  
**Spec**: `specs/002-catalog-graph-architecture/spec.md`  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Incorporación de dependencias de API, configuración de Docker Compose para PostgreSQL local y ajustes base de Django.

- [x] T001 Agregar dependencias django-ninja>=1.3.0 y pydantic>=2.10 en pyproject.toml y sincronizar entorno virtual con uv sync
- [x] T002 [P] Crear archivo docker-compose.yml en la raíz del proyecto para PostgreSQL 17 desechable en desarrollo local con servicio db y volumen postgres_data
- [x] T003 [P] Crear script utilitario de control de base de datos en scripts/db_dev.sh para iniciar, detener y resetear el contenedor Docker de PostgreSQL
- [x] T004 [P] Registrar la aplicación catalog y configurar middleware CORS en config/settings.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Estructura de paquetes, enumeraciones de dominio y punto de montaje de la API que DEBEN existir antes de implementar las historias de usuario.

**⚠️ CRITICAL**: Ninguna historia de usuario puede implementarse sin estas definiciones base.

- [x] T005 Crear la estructura del módulo de catálogo en src/catalog/__init__.py y src/catalog/apps.py configurando CatalogConfig
- [x] T006 [P] Definir enumeraciones de dominio ProductType y RelationshipType en src/catalog/enums.py
- [x] T007 [P] Configurar el punto de entrada de Django Ninja en src/catalog/api.py y montarlo en config/urls.py bajo la ruta /api/

**Checkpoint**: Base técnica lista: módulo de catálogo registrado, enums de negocio disponibles y router de API configurado.

---

## Phase 3: User Story 1 - Modelado y Consulta del Grafo de Compatibilidades Eléctricas (Priority: P1) 🎯 MVP

**Goal**: Implementar las entidades `Product` y `ProductCompatibility`, garantizar restricciones de integridad a nivel de base de datos (`prevent_self_relation`, `unique_source_target_rel_type`), habilitar índices compuestos e incorporar comando de datos semilla reales.

**Independent Test**: Consultar compatibilidades directas de un producto contenedor hacia sus componentes y accesorios en la dirección correcta (`source` -> `target`), y verificar que se rechacen auto-relaciones y duplicados.

### Tests for User Story 1 ⚠️

- [x] T008 [P] [US1] Crear pruebas unitarias para restricciones de integridad en src/catalog/tests/test_models.py validando rechazo de auto-relación y duplicados

### Implementation for User Story 1

- [x] T009 [US1] Implementar modelos Product y ProductCompatibility con constraints e índices compuestos en src/catalog/models.py
- [x] T010 [US1] Generar y aplicar migraciones iniciales del catálogo en src/catalog/migrations/0001_initial.py
- [x] T011 [P] [US1] Implementar métodos directos de compatibilidad get_compatible_components y get_accessories en src/catalog/models.py
- [x] T012 [US1] Crear comando de datos semilla en src/catalog/management/commands/seed_electrical_catalog.py poblando tableros, interruptores y accesorios reales

**Checkpoint**: User Story 1 (MVP) completada: grafo relacional dirigido funcional en base de datos con restricciones validadas y datos semilla disponibles.

---

## Phase 4: User Story 2 - Arquitectura Modular y Optimización de Consultas sin N+1 (Priority: P2)

**Goal**: Implementar capa de selectores con `Prefetch` para resolver árboles de compatibilidad completos en exactamente 2 consultas SQL y exponer la API REST tipada con Django Ninja y documentación OpenAPI.

**Independent Test**: Invocar `get_product_compatibility_tree` y el endpoint `GET /api/v1/catalog/products/{sku}/tree/`, verificando que el conteo de consultas SQL no exceda 2 y que la respuesta contenga los componentes y accesorios correctos.

### Tests for User Story 2 ⚠️

- [x] T013 [P] [US2] Crear pruebas de rendimiento y conteo SQL en src/catalog/tests/test_selectors.py verificando len(connection.queries) <= 2 al obtener el árbol completo
- [x] T014 [P] [US2] Crear pruebas de endpoints y serialización REST en src/catalog/tests/test_api.py validando códigos HTTP 200 y esquemas JSON

### Implementation for User Story 2

- [x] T015 [US2] Implementar capa de selectores de grafo en src/catalog/selectors.py utilizando prefetch_related y select_related para evitar N+1 queries
- [x] T016 [P] [US2] Definir esquemas Pydantic tipados ProductSchema, CompatibilityEdgeSchema y ProductTreeSchema en src/catalog/schemas.py
- [x] T017 [US2] Implementar endpoints REST de catálogo (/products/, /products/{sku}/, /compatibilities/, /tree/) en src/catalog/api.py

**Checkpoint**: User Story 2 completada: capa de lectura desacoplada, consultas SQL optimizadas a 2 queries fijas y API REST documentada en /api/docs.

---

## Phase 5: User Story 3 - Autenticación y Control de Acceso al Catálogo (Priority: P3)

**Goal**: Proteger la gestión técnica del catálogo mediante la interfaz administrativa de Django Admin con soporte para inlines tabulares de aristas de compatibilidad.

**Independent Test**: Iniciar sesión en `/admin/` con credenciales de operador y gestionar productos y aristas de compatibilidad visualmente, validando que usuarios anónimos tengan el acceso denegado.

### Tests for User Story 3 ⚠️

- [x] T018 [P] [US3] Crear pruebas de permisos administrativos en src/catalog/tests/test_admin.py verificando control de acceso para creación y edición de productos

### Implementation for User Story 3

- [x] T019 [US3] Configurar ProductAdmin con ProductCompatibilityInline, filtros por product_type y búsqueda por sku en src/catalog/admin.py

**Checkpoint**: User Story 3 completada: gobernanza administrativa y control de acceso funcional en Django Admin.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentación técnica, actualización de checklists operativos y validación integral de calidad.

- [x] T020 [P] Documentar la arquitectura del grafo de catálogo y ejemplos de consulta en docs/catalog-architecture.md
- [x] T021 [P] Actualizar checklist operativo en docs/basic-todo.md reflejando el cierre de la arquitectura base y datos de la Fase 3
- [x] T022 Ejecutar la validación integral de pruebas con uv run python manage.py test src/catalog/tests y validación de linters con uv run ruff check .

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup (T001-T004)
     │
     ▼
Phase 2: Foundational (T005-T007)
     │
     ├───────────────────────┬───────────────────────┐
     ▼                       ▼                       ▼
Phase 3: User Story 1 (P1)  Phase 4: User Story 2 (P2) Phase 5: User Story 3 (P3)
[T008-T012] 🎯 MVP         [T013-T017]             [T018-T019]
     │                       │                       │
     └───────────────────────┴───────────────────────┘
                             │
                             ▼
              Phase 6: Polish & Verification (T020-T022)
```

### User Story Dependencies

- **User Story 1 (P1)**: Requiere Fase 1 y Fase 2 completadas. Establece los modelos y migraciones indispensables para todas las historias.
- **User Story 2 (P2)**: Requiere los modelos y migraciones de US1 (T009-T010) para implementar los selectores de grafo y la API REST.
- **User Story 3 (P3)**: Requiere los modelos de US1 (T009) para registrar el `ProductAdmin` e inlines.
- **Polish (Fase 6)**: Requiere que US1, US2 y US3 estén implementadas antes de ejecutar la validación global en T022.

---

## Parallel Opportunities

- **Fase 1 (Setup)**: T002 (`docker-compose.yml`), T003 (`db_dev.sh`) y T004 (`settings.py`) pueden desarrollarse en paralelo tras T001.
- **Fase 2 (Foundational)**: T006 (`enums.py`) y T007 (`api.py`) pueden ejecutarse en paralelo.
- **Historias de Usuario**:
  - T008 (test de modelos) y T011 (métodos de modelo) pueden desarrollarse en paralelo con T012 (script de seed data).
  - T013 (test de selectores) y T014 (test de API) pueden crearse en paralelo antes de la implementación de T015-T017.
  - T018 (test de admin) y T020 (documentación) pueden ejecutarse en paralelo.

---

## Parallel Example: User Story 1 & 2 Tests

```bash
# Desarrollar pruebas en paralelo antes de la implementación:
Task: "T008 [P] [US1] Crear pruebas unitarias para restricciones de integridad en src/catalog/tests/test_models.py"
Task: "T013 [P] [US2] Crear pruebas de rendimiento y conteo SQL en src/catalog/tests/test_selectors.py"
Task: "T014 [P] [US2] Crear pruebas de endpoints y serialización REST en src/catalog/tests/test_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Fase 1 (Setup) y Fase 2 (Foundational).
2. Implementar Fase 3 (User Story 1): Modelos `Product` y `ProductCompatibility`, migraciones, restricciones de integridad y comando de datos semilla `seed_electrical_catalog`.
3. **Punto de Control MVP**: Ejecutar pruebas de modelo (`test_models.py`) y sembrar datos de prueba para validar que el grafo dirigido en SQL opera con exactitud.

### Incremental Delivery

1. **Incremento 1 (MVP)**: Grafo relacional de catálogo operativo en base de datos con restricciones forzadas (US1).
2. **Incremento 2 (Consultas y API)**: Selectores optimizados sin N+1 y endpoints REST con Django Ninja documentados en Swagger (US2).
3. **Incremento 3 (Gobernanza Administrativa)**: Gestión visual y permisos en Django Admin (US3).
4. **Cierre Definitivo**: Validación integral de calidad, linters en verde y documentación técnica consolidada.
