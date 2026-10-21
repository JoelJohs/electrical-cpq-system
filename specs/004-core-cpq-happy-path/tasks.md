# Tasks: Flujo Principal de Configuración, Validación Eléctrica y Cotizaciones Técnicas (Fase 4 - Happy Path)

**Input**: Documentos de diseño desde `specs/004-core-cpq-happy-path/` (`plan.md`, `spec.md`, `data-model.md`, `research.md`, `contracts/`, `quickstart.md`).  
**Prerequisites**: Fase 3 completada (Catálogo y grafo relacional en `src/catalog/` operativo).  
**Directriz de Negocio**: Cero precios, cero monedas, cero impuestos en base de datos. CPQ técnico centrado en viabilidad física y despiece exacto (BOM).

---

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Ejecutable en paralelo (archivos independientes sin bloqueos de tareas previas).
- **[Story]**: Historia de usuario a la que pertenece ([US1], [US2], [US3], [US4]).
- Cada tarea contiene rutas de archivo explícitas y concretas.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del módulo de cotizaciones técnicas y configuración base en el proyecto.

- [x] T001 Crear la estructura de directorios del módulo de cotizaciones en src/quotes/__init__.py, src/quotes/apps.py, src/quotes/templates/quotes/ y src/quotes/tests/__init__.py
- [x] T002 Registrar la aplicación quotes.apps.QuotesConfig en INSTALLED_APPS dentro de config/settings.py y verificar configuración del directorio de templates
- [x] T003 [P] Crear fixtures y utilidades base de prueba en src/quotes/tests/conftest.py para generar cotizaciones y productos semilla reutilizables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Entidades relacionales base y persistencia que DEBEN existir antes de implementar cualquier historia de usuario.

**⚠️ CRITICAL**: Ninguna historia de usuario puede implementarse sin estas definiciones de base de datos.

- [x] T004 Definir la enumeración de dominio QuoteStatus (DRAFT, VALIDATED, SENT, ACCEPTED, CANCELLED) en src/quotes/enums.py
- [x] T005 [P] Implementar modelo Quote en src/quotes/models.py con campos folio (CharField unique, db_index), client_name, project_reference, status (choices=QuoteStatus.choices, default=DRAFT), is_board_assembly (bool), board_product (ForeignKey Product, null=True, blank=True, on_delete=SET_NULL), notes y timestamps
- [x] T006 [P] Implementar modelo QuoteItem en src/quotes/models.py con quote (ForeignKey Quote, on_delete=CASCADE), product (ForeignKey Product, on_delete=PROTECT), quantity (PositiveIntegerField, default=1), slot_position (PositiveIntegerField, null=True, blank=True), notes y constraint UniqueConstraint(fields=['quote', 'product', 'slot_position'], name='unique_quote_product_slot')
- [x] T007 Generar y aplicar migraciones iniciales de cotizaciones en src/quotes/migrations/0001_initial.py ejecutando uv run python manage.py makemigrations quotes y uv run python manage.py migrate

**Checkpoint**: Base de datos lista: modelos Quote y QuoteItem migrados con restricciones de integridad y protección de catálogo.

---

## Phase 3: User Story 1 - Elaboración de Cotizaciones Técnicas y Selección Asistida (Priority: P1) 🎯 MVP

**Goal**: Permitir crear cotizaciones técnicas, agregar partidas de productos con cantidades y consultar sugerencias de accesorios complementarios (`COMPLEMENT_OF`) sin importes monetarios.

**Independent Test**: Crear una cotización para un cliente, agregar interruptores con cantidades, verificar persistencia de partidas y consultar accesorios complementarios sugeridos.

### Tests for User Story 1 ⚠️

- [x] T008 [P] [US1] Crear pruebas unitarias de persistencia y restricciones en src/quotes/tests/test_models.py validando generación de folio, estados válidos y rechazo de duplicados en ranuras
- [x] T009 [P] [US1] Crear pruebas unitarias de servicios y selectores de cotización en src/quotes/tests/test_services.py verificando creación de cotizaciones y adición de partidas

### Implementation for User Story 1

- [x] T010 [US1] Implementar servicios de creación de cotización y mutación de partidas (create_quote, add_item_to_quote, remove_quote_item, update_quote_item_quantity) con transacciones atómicas en src/quotes/services.py
- [x] T011 [P] [US1] Implementar selectores de cotizaciones y consulta de accesorios complementarios (get_quote_by_id, get_quote_by_folio, get_quote_items, get_quote_suggested_complements) en src/quotes/selectors.py

**Checkpoint**: User Story 1 (MVP) completada: cotizaciones técnicas y partidas persistentes con soporte para sugerencias de complementos.

---

## Phase 4: User Story 2 - Motor de Validación de Restricciones Técnicas y Despiece BOM (Priority: P2) 🎯 Core Técnico

**Goal**: Validar en tiempo real las restricciones de tableros (alojamiento `COMPATIBLE_WITH`, capacidad de espacios $\sum(\text{polos} \times \text{cant}) \le \text{espacios}$, corriente máxima y dependencias obligatorias `REQUIRES` con prevención de ciclos) y emitir el BOM exacto.

**Independent Test**: Configurar un ensamble con exceso de ranuras o falta de accesorio obligatorio y verificar que devuelva `valid: false` con errores estructurados; al corregir las partidas, verificar `valid: true` y generar el BOM con cantidades y SKUs exactos.

### Tests for User Story 2 ⚠️

- [X] T012 [P] [US2] Crear pruebas unitarias del motor de validación y detección de ciclos en src/quotes/tests/test_rules.py cubriendo espacios, amperajes, aristas REQUIRES faltantes y resolución mutua sin recursión infinita
- [X] T013 [P] [US2] Crear pruebas unitarias de exactitud de la Lista de Materiales (BOM) en src/quotes/tests/test_bom.py verificando agregación determinista y conservación de cantidades

### Implementation for User Story 2

- [X] T014 [US2] Implementar motor de validación técnica de reglas electro-mecánicas y cierre transitivo de REQUIRES en src/quotes/rules.py emitiendo respuestas tipadas con códigos INSUFFICIENT_SPACE, AMPERAGE_EXCEEDED, MISSING_REQUIRED_ACCESSORY
- [X] T015 [US2] Implementar selector de generación y agregación de Lista de Materiales (get_quote_bom) en src/quotes/selectors.py consolidando gabinete, derivados y accesorios con SKUs y cantidades exactas

**Checkpoint**: User Story 2 completada: motor de reglas operando en memoria (< 50ms) con reporte de errores cuantitativos y generación de BOM.

---

## Phase 5: User Story 3 - API Tipada del Configurador y Transiciones de Estado (Priority: P3)

**Goal**: Exponer endpoints REST en Django Ninja para crear, modificar, validar cotizaciones, transicionar estados (`DRAFT` → `VALIDATED` → `SENT` → `ACCEPTED`) y exportar BOM con documentación interactiva Swagger.

**Independent Test**: Realizar peticiones HTTP completas a `/api/v1/quotes/` validando respuestas JSON, códigos HTTP y bloqueo de edición en estados inmutables.

### Tests for User Story 3 ⚠️

- [X] T016 [P] [US3] Crear pruebas de integración HTTP y contratos de endpoints en src/quotes/tests/test_api.py validando códigos 200, 201, 404, 409 y esquemas JSON

### Implementation for User Story 3

- [X] T017 [P] [US3] Definir esquemas Pydantic v2 en src/quotes/schemas.py (CreateQuoteSchema, QuoteDetailSchema, AddQuoteItemSchema, ValidationResultSchema, BOMResponseSchema)
- [X] T018 [US3] Implementar endpoints REST de cotizaciones y validación (/quotes/, /quotes/{id}/, /quotes/{id}/items/, /quotes/{id}/validate/, /quotes/{id}/bom/) en src/quotes/api.py y montar el router en config/urls.py
- [X] T019 [US3] Implementar lógica de transición de estados y bloqueo de modificaciones en estado de solo lectura (transition_quote_status) en src/quotes/services.py

**Checkpoint**: User Story 3 completada: contratos REST documentados en Swagger en /api/docs y máquina de estados transaccional protegida.

---

## Phase 6: User Story 4 - Interfaces Web Asistidas con Django Templates + Tailwind + Alpine.js (Priority: P4)

**Goal**: Construir las interfaces interactivas de autoservicio: vista rápida comercial para ventas y configurador técnico de tableros para integradores con cálculo dinámico de ranuras y exportación de BOM.

**Independent Test**: Navegar a `/quotes/new/` y `/quotes/<id>/configurator/`, interactuar con la barra reactiva de ocupación de polos de Alpine.js y ejecutar validación asíncrona con HTMX.

### Tests for User Story 4 ⚠️

- [X] T020 [P] [US4] Crear pruebas de renderizado de vistas web y respuestas HTML en src/quotes/tests/test_views.py

### Implementation for User Story 4

- [X] T021 [P] [US4] Diseñar layout base corporativo con Tailwind CSS y Alpine.js/HTMX en src/quotes/templates/quotes/base_quotes.html incorporando paleta de colores y logo SVG de ABV Electric Supply conforme a DESIGN.md
- [X] T022 [P] [US4] Implementar plantilla de vista comercial rápida con panel lateral reactivo de sugerencias en src/quotes/templates/quotes/quick_quote.html
- [X] T023 [US4] Implementar plantilla del configurador técnico de tableros con indicador dinámico de espacios y chasis 2D en src/quotes/templates/quotes/configurator.html
- [X] T024 [P] [US4] Implementar plantilla de resumen de Lista de Materiales (BOM) formateada para taller e impresión en src/quotes/templates/quotes/bom_detail.html
- [X] T025 [US4] Implementar controladores de vistas web en src/quotes/views.py y registrar rutas en src/quotes/urls.py vinculadas a config/urls.py

**Checkpoint**: User Story 4 completada: ambas interfaces web interactivas y reactivas operativas en el navegador.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Gobernanza administrativa, verificación automatizada integral y actualización del roadmap.

- [X] T026 [P] Configurar administración en src/quotes/admin.py con QuoteAdmin e inlines tabulares QuoteItemInline
- [X] T027 [P] Crear script de verificación automatizada de la Fase 4 en scripts/check_phase4.sh validando modelos, motor de reglas, endpoints REST y vistas web
- [X] T028 [P] Actualizar el checklist operativo en docs/basic-todo.md reflejando el estado de avance de la Fase 4
- [X] T029 Ejecutar validación integral del proyecto con uv run python manage.py test y linters con uv run ruff check . y uv run ruff format --check .

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup (T001-T003)
     │
     ▼
Phase 2: Foundational (T004-T007)
     │
     ├───────────────────────┬───────────────────────┐
     ▼                       ▼                       ▼
Phase 3: US1 (P1) 🎯 MVP    Phase 4: US2 (P2)       Phase 5: US3 (P3)
[T008-T011]                 [T012-T015]             [T016-T019]
     │                       │                       │
     └───────────────────────┴───────────────────────┘
                             │
                             ▼
                    Phase 6: US4 (P4)
                    [T020-T025]
                             │
                             ▼
                    Phase 7: Polish
                    [T026-T029]
```

### User Story Dependencies

- **User Story 1 (P1)**: Depende únicamente de la Fase 2 (Modelos Quote y QuoteItem migrados).
- **User Story 2 (P2)**: Depende de US1 (partidas y cotizaciones) y consume el grafo de catálogo de la Fase 3.
- **User Story 3 (P3)**: Expone los casos de uso de US1 y US2 mediante Django Ninja.
- **User Story 4 (P4)**: Construye las interfaces web consumiendo los servicios y selectores de US1, US2 y US3.

---

## Parallel Opportunities

- **Setup & Foundational**: T003, T005, T006 pueden desarrollarse en paralelo antes de la migración T007.
- **User Story 1**: T008 (tests modelos), T009 (tests servicios) y T011 (selectores) pueden prepararse en paralelo con T010.
- **User Story 2**: T012 (tests de reglas) y T013 (tests BOM) se escriben en paralelo antes de implementar el motor T014 y selector T015.
- **User Story 3**: T016 (tests API) y T017 (esquemas Pydantic) pueden desarrollarse simultáneamente.
- **User Story 4**: T021 (layout base), T022 (plantilla comercial), T024 (plantilla BOM) pueden maquetarse en paralelo.
- **Polish**: T026, T027 y T028 son completamente independientes entre sí.

---

## Implementation Strategy

### MVP First (User Story 1 + Motor de Reglas US2)
1. Completar Setup (T001-T003) y Foundational (T004-T007).
2. Implementar US1 (T008-T011): Crear cotización técnica, agregar partidas y consultar complementos.
3. Implementar US2 (T012-T015): Validar restricciones electro-mecánicas y emitir el BOM.
4. **Validación en Shell / Tests**: Verificar que el cálculo de espacios, corriente y dependencias obligatorias funcione con 0 errores antes de pasar a la UI.

### Entrega Incremental
1. **Incremento 1**: Modelos y motor de validación en backend (US1 + US2) con tests en verde.
2. **Incremento 2**: Endpoints REST con Django Ninja y Swagger interactivo (US3).
3. **Incremento 3**: Interfaces web con Django Templates, Tailwind CSS y reactividad con Alpine.js/HTMX (US4).
4. **Incremento 4**: Script `check_phase4.sh`, administración en Django Admin y documentación (Polish).
