# Implementation Plan: Flujo Principal de Configuración, Validación Eléctrica y Cotizaciones Técnicas (Fase 4 - Happy Path)

**Branch**: `004-core-cpq-happy-path` | **Date**: 2026-10-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-core-cpq-happy-path/spec.md`

---

## Summary

Implementar el flujo principal (*Happy Path*) del CPQ Técnico para **ABV ELECTRIC SUPPLY**: creación y gestión de cotizaciones técnicas (`Quote`, `QuoteItem`), motor de validación en tiempo real de restricciones electro-mecánicas (espacios/polos, amperajes y dependencias obligatorias `REQUIRES`), generación automatizada de Listas de Materiales (*BOM*), endpoints REST documentados en Django Ninja y dos interfaces web asistidas con Django Templates, Tailwind CSS y Alpine.js / HTMX para ejecutivos comerciales e ingenieros integradores.

**Directriz de Dominio Confirmada**: La base de datos y la aplicación **no gestionan precios monetarios, divisas ni impuestos (IVA)**; el sistema opera como un validador de configuración física y despiece técnico de ingeniería.

---

## Technical Context

**Language/Version**: Python >= 3.14  
**Primary Dependencies**:
- `django>=6.1.1` (Framework web y ORM)
- `django-ninja>=1.3.0` (API REST tipada con OpenAPI/Swagger)
- `pydantic>=2.10` (Validación de esquemas y contratos de datos)
- `django-cors-headers>=4.7.0` (Políticas de seguridad CORS)
- Frontend client-side: Tailwind CSS, Alpine.js >= 3.x, HTMX >= 1.9.x  
**Storage**: PostgreSQL 17 (vía Docker Compose local y VPS) con fallback transparente a SQLite para ejecución ágil de pruebas unitarias  
**Testing**: Django Test Framework (`uv run python manage.py test`)  
**Target Platform**: Linux Server (Ubuntu 24.04 LTS), desarrollo local Linux  
**Project Type**: Monolito modular (Django Web Service + Server-Side Rendered Interactive Views + REST API)  
**Performance Goals**:
- Validación de reglas técnicas y generación de BOM en **< 2 segundos** para cotizaciones con hasta 50 partidas.
- Consultas de lectura y resolución de árbol de compatibilidad en **$\le 2$ consultas SQL fijas**.  
**Constraints**:
- **Cero importes monetarios**: Ningún modelo o endpoint contemplará precios o cálculo de impuestos.
- **Autoridad en el servidor**: El frontend nunca valida de forma exclusiva; el backend es la autoridad final de las reglas.
- **Transacciones atómicas**: Mutaciones de cotización y partidas protegidas con `transaction.atomic()`.  
**Scale/Scope**:
- 2 perfiles de usuario principales (Ejecutivo de Ventas e Ingeniero Integrador).
- Catálogo base multimarca (familias NQ, QO, EDB y accesorios).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Arquitectura Limpia y Modularidad**: La lógica de cotizaciones se aísla en la nueva aplicación `src/quotes/`, separando dominio (`models.py`), reglas (`rules.py`), casos de uso (`services.py`), lectura (`selectors.py`), presentación API (`api.py`, `schemas.py`) y presentación web (`views.py`, `templates/quotes/`).
- [x] **Reutilización del Grafo Existente**: Se consumen las aristas de `ProductCompatibility` de la Fase 3 (`COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`) sin alterar el catálogo ni duplicar tablas de nodos.
- [x] **YAGNI (You Aren't Gonna Need It)**: Eliminación explícita de precios, divisas, pasarelas de pago y facturación.
- [x] **Test-Driven & Verificabilidad**: Cobertura obligatoria para reglas de espacios, límites de corriente, dependencias obligatorias (`REQUIRES`), inmutabilidad de estados y contratos de API.

---

## Project Structure

### Documentation (this feature)

```text
specs/004-core-cpq-happy-path/
├── spec.md                  # Especificación funcional aprobada
├── plan.md                  # Este plan de implementación arquitectónico
├── research.md              # Decisiones técnicas y análisis de alternativas
├── data-model.md            # Entidades relacionales, constraints y estados
├── quickstart.md            # Guía de validación y escenarios reproducibles
├── checklists/
│   └── requirements.md      # Checklist de calidad de requisitos (100% aprobado)
└── contracts/
    ├── quotes-api.md        # Contrato de endpoints REST Django Ninja
    ├── validation-engine.md # Contrato algorítmico y códigos de error del motor
    └── bom-contract.md      # Contrato de Lista de Materiales (BOM)
```

### Source Code Layout (`src/quotes/`)

```text
src/
├── catalog/                 # Aplicación existente (Fase 3: Grafo de Productos y Compatibilidades)
│   ├── models.py
│   ├── enums.py
│   ├── selectors.py
│   ├── api.py
│   └── ...
└── quotes/                  # Nueva aplicación (Fase 4: CPQ Técnico y Cotizaciones)
    ├── __init__.py
    ├── apps.py              # QuotesConfig
    ├── models.py            # Quote, QuoteItem, QuoteStatus
    ├── rules.py             # Motor algorítmico de validación electro-mecánica y REQUIRES
    ├── services.py          # Servicios transaccionales (crear, agregar partida, transicionar estado)
    ├── selectors.py         # Consultas optimizadas y generador de BOM (get_quote_bom)
    ├── schemas.py           # Esquemas Pydantic v2 para Django Ninja
    ├── api.py               # Router REST montado en /api/v1/quotes
    ├── views.py             # Vistas Django para interfaz comercial y configurador de tableros
    ├── urls.py              # Rutas web para las vistas de usuario
    ├── templates/
    │   └── quotes/
    │       ├── base_quotes.html    # Layout base con Tailwind CSS y Alpine.js
    │       ├── quick_quote.html    # Módulo 1: Vista rápida comercial para ventas
    │       └── configurator.html   # Módulo 2: Configurador de tableros para integradores
    ├── admin.py             # QuoteAdmin con QuoteItemInline
    ├── migrations/          # 0001_initial.py
    └── tests/
        ├── test_models.py       # Pruebas de persistencia y restricciones de unicidad
        ├── test_rules.py        # Pruebas de reglas de espacios, amperaje y ciclos REQUIRES
        ├── test_services.py     # Pruebas de transiciones de estado e inmutabilidad
        ├── test_selectors.py    # Pruebas de exactitud del BOM
        ├── test_api.py          # Pruebas de endpoints REST y esquemas Ninja
        └── test_views.py        # Pruebas de renderizado de vistas web
```

---

## Implementation Work Breakdown (Fase 4)

El desarrollo se ejecutará en **6 bloques secuenciales y acoplados lógicamente**:

### Bloque 1: Modelo de Cotizaciones Técnicas y Persistencia
- Crear la aplicación `src/quotes/` y registrarla en `config/settings.py`.
- Definir `QuoteStatus`, `Quote` y `QuoteItem` con restricciones de integridad (`unique_quote_product_slot`, protección `on_delete=PROTECT`).
- Generar y aplicar migraciones iniciales (`0001_initial.py`).
- Implementar pruebas unitarias de persistencia en `src/quotes/tests/test_models.py`.

### Bloque 2: Motor de Reglas Técnicas y Validación
- Implementar pipeline en `src/quotes/rules.py`:
  - `validate_board_assembly(quote)`: Evaluación de anfitrión, ranuras físicas y corriente de barras.
  - Resolución de dependencias obligatorias `REQUIRES` con algoritmo DFS antilazos y detección de ciclos mutuos.
  - Extracción de sugerencias no bloqueantes `COMPLEMENT_OF`.
- Respuestas estructuradas con códigos tipados (`INSUFFICIENT_SPACE`, `AMPERAGE_EXCEEDED`, `MISSING_REQUIRED_ACCESSORY`).
- Implementar pruebas unitarias exhaustivas en `src/quotes/tests/test_rules.py`.

### Bloque 3: Capa de Servicios, Selectores y Generación de BOM
- En `src/quotes/services.py`:
  - `create_quote`, `add_item_to_quote`, `update_quote_item`, `remove_quote_item`, `transition_quote_status`.
  - Enforzar inmutabilidad de cotizaciones en estado `SENT`, `ACCEPTED` o `CANCELLED`.
- En `src/quotes/selectors.py`:
  - `get_quote_by_id`, `get_quote_items`, `get_quote_bom`.
  - Agrupación determinista del despiece de materiales listo para ensamble.
- Implementar pruebas de servicios y selectores en `src/quotes/tests/test_services.py` y `test_selectors.py`.

### Bloque 4: API REST del Configurador (Django Ninja)
- Definir esquemas Pydantic v2 en `src/quotes/schemas.py`.
- Implementar endpoints en `src/quotes/api.py`:
  - `POST /api/v1/quotes/`
  - `GET /api/v1/quotes/`
  - `GET /api/v1/quotes/{id}/`
  - `POST /api/v1/quotes/{id}/items/`
  - `DELETE /api/v1/quotes/{id}/items/{item_id}/`
  - `POST /api/v1/quotes/{id}/validate/`
  - `GET /api/v1/quotes/{id}/bom/`
- Montar el router de cotizaciones en el API global de `config/urls.py`.
- Implementar pruebas de integración HTTP en `src/quotes/tests/test_api.py`.

### Bloque 5: Interfaces Web de Usuario (Ventas e Integradores)
- Crear vistas web en `src/quotes/views.py` y rutas en `src/quotes/urls.py`:
  - `/quotes/`: Listado de cotizaciones técnicas.
  - `/quotes/new/`: Vista comercial rápida de ventas con panel lateral de sugerencias.
  - `/quotes/<id>/configurator/`: Configurador técnico interactivo de tableros con indicador dinámico de espacios.
  - `/quotes/<id>/bom/`: Vista de resumen técnico y lista de despiece para impresión/exportación.
- Diseñar plantillas en `src/quotes/templates/quotes/` con Tailwind CSS y Alpine.js / HTMX.
- Implementar pruebas de renderizado en `src/quotes/tests/test_views.py`.

### Bloque 6: Integración y Cierre de la Fase 4
- Configurar `QuoteAdmin` con inlines en `src/quotes/admin.py`.
- Crear script de verificación automatizada `scripts/check_phase4.sh` (similar a `check_phase2.sh` y `check_phase3.sh`).
- Ejecutar suite completa de pruebas (`uv run python manage.py test`) y linters (`uv run ruff check .`).
- Actualizar el checklist operativo en `docs/basic-todo.md`.

---

## Complexity Tracking

| Decisión | Justificación | Alternativa Más Simple Rechazada Porque |
| :--- | :--- | :--- |
| **Separación de `src/quotes/` como app independiente** | Desacopla las transacciones y cotizaciones del catálogo estático de productos (`src/catalog/`), manteniendo alta cohesión y bajo acoplamiento. | Dejar todo en `src/catalog/` crearía un módulo sobredimensionado mezclando datos maestros de productos con cotizaciones transaccionales de clientes. |
| **Algoritmo DFS con recursion stack para `REQUIRES`** | Garantiza la detección rigurosa de componentes obligatorios encadenados y previene cuelgues o recursiones infinitas ante dependencias mutuas. | Validaciones simples de 1 nivel ignorarían accesorios de segundo orden que son mandatorios para la operación segura. |
