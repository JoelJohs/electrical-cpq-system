# Implementation Plan: Arquitectura Base y Catálogo en Grafo Dirigido (Fase 3)

**Branch**: `002-catalog-graph-architecture` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-catalog-graph-architecture/spec.md`

## Summary

Implementar la **Fase 3: Arquitectura Base y Datos** centrada en el catálogo técnico de productos eléctricos para el sistema CPQ. El plan abarca la creación del modelo de datos de grafo relacional dirigido en SQL (`Product` y `ProductCompatibility`), una arquitectura modular en Django (dominio, selectores de consultas en grafo sin problema de N+1 queries, capa de servicios y API REST documentada con Django Ninja), autenticación nativa con Django Admin, y un entorno local de PostgreSQL desechable y reproducible mediante Docker Compose.

## Technical Context

**Language/Version**: Python >=3.14 (aislado herméticamente mediante `uv`).

**Primary Dependencies**: Django >=6.1.1, django-ninja >=1.3.0, psycopg[binary] >=3.3.6, django-environ >=0.14.0, pydantic >=2.10.

**Storage**: PostgreSQL 17 (contenedor local desechable con Docker Compose / VPS producción) configurado mediante `DATABASE_URL`. Compatible con SQLite en ejecuciones de pruebas locales rápidas.

**Testing**: Django TestCase / TestRunner (`uv run python manage.py test`), Ruff linter y formateador.

**Target Platform**: Linux (Ubuntu 24.04 LTS en VPS / Docker local).

**Project Type**: Servicio web backend / API RESTful para CPQ eléctrico.

**Performance Goals**:
- Consultas de compatibilidad directa en menos de 10 milisegundos con índices compuestos.
- Recuperación del árbol completo (Tablero + Componentes + Accesorios) en un número fijo y acotado de consultas SQL (exactamente 2 consultas mediante `Prefetch`).
- Carga de API y renderizado JSON en menos de 30 milisegundos.

**Constraints**:
- Prohibición estricta del campo `is_bidirectional`: la relación siempre viaja de contenedor/anfitrión (`source`) a componente/accesorio (`target`).
- Integridad forzada en el motor de base de datos (`CheckConstraint` contra auto-relaciones y `UniqueConstraint` contra aristas duplicadas).
- Sin dependencias de servicios SaaS externos para autenticación en esta fase (uso de autenticación nativa de Django).
- Entorno de base de datos local 100% desechable mediante Docker para pruebas destructivas sin riesgo.

**Scale/Scope**: Catálogo inicial para equipos de distribución eléctrica (tableros, interruptores, accesorios) listo para alimentar el motor de cotización en la Fase 4.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Justificación |
|-----------|--------|---------------|
| **I. Simplicidad & YAGNI** | PASS | Uso de 2 tablas relacionales en PostgreSQL para modelar el grafo en lugar de motores de grafos independientes (Neo4j). |
| **II. Sin Bidireccionalidad Falsa** | PASS | La relación dirigida preserva la semántica física y habilita optimizaciones ORM nativas (`prefetch_related`). |
| **III. Integridad por Diseño** | PASS | Restricciones de comprobación y unicidad aplicadas a nivel de esquema de base de datos e índices B-Tree compuestos. |
| **IV. Aislamiento & Modularidad** | PASS | Separación limpia entre modelos (dominio), selectores (lectura/grafo), servicios (mutación) y presentación (API Ninja). |

## Project Structure

### Documentation (this feature)

```text
specs/002-catalog-graph-architecture/
├── spec.md                  # Especificación de requerimientos y criterios de aceptación
├── plan.md                  # Este archivo (Plan de implementación técnica)
├── research.md              # Fase 0: Decisiones sobre grafo, Django Ninja y PostgreSQL Docker
├── data-model.md            # Fase 1: Entidades Product, ProductCompatibility, índices y constraints
├── quickstart.md            # Fase 1: Guía paso a paso de validación y seed data
├── checklists/
│   └── requirements.md      # Lista de verificación de calidad de la especificación
└── contracts/               # Fase 1: Contratos de interfaz
    ├── catalog-api.md       # Contrato de endpoints REST y esquemas JSON Ninja
    ├── database-schema.md   # Contrato DDL y restricciones de PostgreSQL
    └── docker-compose.md    # Contrato del contenedor Docker de base de datos
```

### Source Code (repository root)

```text
.
├── docker-compose.yml                 # Contenedor PostgreSQL 17 desechable para desarrollo local
├── pyproject.toml                     # Dependencias (django, django-ninja, psycopg)
├── config/
│   ├── settings.py                    # Configuración de base de datos, apps y CORS
│   └── urls.py                        # Montaje de API Ninja (/api/) y Django Admin
├── src/
│   └── catalog/                       # Aplicación modular del catálogo eléctrico
│       ├── __init__.py
│       ├── apps.py                    # Configuración de la aplicación
│       ├── models.py                  # Product, ProductCompatibility, Enums, Constraints
│       ├── selectors.py               # Consultas optimizadas de grafo sin N+1
│       ├── services.py                # Lógica de validación y mutación de catálogo
│       ├── api.py                     # Router y esquemas Django Ninja (/api/v1/catalog)
│       ├── admin.py                   # Configuración de Django Admin con inlines
│       ├── management/
│       │   └── commands/
│       │       └── seed_electrical_catalog.py  # Carga de datos reales de prueba
│       └── tests/
│           ├── __init__.py
│           ├── test_models.py         # Pruebas de restricciones de base de datos
│           ├── test_selectors.py      # Pruebas de consultas de grafo y conteo SQL
│           └── test_api.py            # Pruebas de endpoints REST y esquemas Ninja
└── scripts/
    └── db_dev.sh                      # Script utilitario para arrancar/resetear Docker DB
```

**Structure Decision**: Aplicación modular `catalog` dentro de `src/catalog/` siguiendo el patrón Domain-Selector-Service-API, con endpoints expuestos mediante Django Ninja en `/api/` y administración en `/admin/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *Ninguna* | Diseño mínimo y desacoplado | N/A |
