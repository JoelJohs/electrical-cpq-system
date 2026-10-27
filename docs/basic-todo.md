# Roadmap Operativo y Checklist del Proyecto (Basic-TODO)

> **Proyecto**: Sistema Web de Selección Basado en Reglas para la Recomendación de Piezas Compatibles y Armado de Tableros Eléctricos (CPQ)  
> **Organización Receptora**: ABV ELECTRIC SUPPLY (Morelia, Michoacán)  
> **Residente**: Joel Josafat Hernández Saucedo | **Asesor Externo**: Ing. Octavio Trinidad Rodríguez Ramírez (Encargado de TI)  
> **Periodo de Ejecución**: 6 meses (01 de Agosto de 2026 – 18 de Diciembre de 2026)  
> **Documento Fuente**: Bosquejo Inicial de Residencias Profesionales (`BOSQUEJO - Joel Josafat Hernández Saucedo-1.pdf`)  
> **Especificación de Producto**: [`PRODUCT.md`](../PRODUCT.md) | **Lineamientos UI**: [`DESIGN.md`](../DESIGN.md)

---

## 1. Tablero General de Avance del Roadmap

| Fase / Mes | Nombre de la Fase | Enfoque Principal | Estado | Evidencia / Validación |
| :---: | :--- | :--- | :---: | :--- |
| **Fase 1**<br>*(Mes 1)* | **Alineación, Alcance y Matrices** | Matriz de compatibilidad electro-mecánica, perfiles de usuario (Ventas / Integradores) y PRD. | 🟡 En Curso | PRD y PRODUCT.md completos; pendiente validación formal de matriz técnica de ingeniería. |
| **Fase 2**<br>*(Mes 2)* | **Configuración Inicial y Repositorio** | Repositorio Git, CI/CD, linters Ruff, pre-commit y plantillas de aprovisionamiento VPS. | 🟢 Operativo | `./scripts/check_phase2.sh --local` (15 PASS · 0 FAIL). Guía en `docs/deployment-vps.md`. |
| **Fase 3**<br>*(Mes 2-3)* | **Arquitectura Base y Grafo de Datos** | Modelado relacional en grafo SQL, selectores O(1), API REST Ninja, Docker Postgres 17. | 🟢 Operativo | `./scripts/check_phase3.sh` (9 PASS · 0 FAIL). 37 tests en verde. Guía en `docs/catalog-architecture.md`. |
| **Fase 4**<br>*(Mes 3-4)* | **Desarrollo del Core (Happy Path)** | Asistente de compatibilidad en vivo, reglas técnicas, BOM en memoria y despiece en tiempo real. | 🟢 Operativo | 37 tests unitarios/integración en verde (`uv run python manage.py test src.catalog.tests tests`). UI en `/`. |
| **Fase 5**<br>*(Mes 5)* | **QA, Integración y Casos Reales** | Validación funcional con **30 casos reales de cotización**, verificación de latencia < 2s y 0% incompatibilidades. | ⚪ **Siguiente Paso** | Batería de pruebas con área de ingeniería y ejecutivos comerciales de ABV. |
| **Fase 6**<br>*(Mes 6)* | **Despliegue Staging y Cierre** | Despliegue en VPS Ubuntu 24.04 LTS, capacitación de usuarios, manuales y entrega del Reporte Final. | ⚪ Pendiente | Despliegue funcional en staging, manuales operativos y reporte final acreditado. |

---

## 2. Detalle de Fases y Actividades Operativas

### Fase 1: Alineación, Alcance y Matrices Técnicas (Mes 1)
*Objetivo: Formalizar el conocimiento empírico de ingeniería en matrices de compatibilidad sin ambigüedades.*

- [x] Definir el problema comercial/operativo y formalizar el alcance en `PRODUCT.md` y `DESIGN.md`.
- [x] Delimitar las fronteras del software (*Out of Scope* explícito en PDF):
  - [x] Sin e-commerce transaccional con pasarelas de pago ni tarjetas de crédito.
  - [x] Sin timbrado fiscal ni facturación electrónica CFDI/SAT.
  - [x] Cero precios monetarios en base de datos (despiece y compatibilidad técnica pura).
- [ ] Consolidar y firmar con Ingeniería la matriz de compatibilidades prioritarias:
  - [ ] Tableros y centros de carga (familias NQ, QO, EDB).
  - [ ] Módulos de fuerza y protecciones (interruptores termomagnéticos 1P, 2P, 3P).
  - [ ] Accesorios obligatorios (`REQUIRES`: zapatas, kits de montaje, bases).
  - [ ] Accesorios complementarios (`COMPLEMENT_OF`: contactos auxiliares, bobinas de disparo, señalización).
  - [ ] Alternativas de sustitución técnica (`ALTERNATIVE_TO`: equivalencias entre marcos o series).
- [x] Definir los 2 flujos operativos de usuario (*User Journeys*):
  - [x] **Ejecutivo Comercial / Ventas**: Búsqueda rápida en mostrador, recomendación obligatoria de refacciones y venta cruzada (*cross-selling*).
  - [x] **Ingeniero Integrador de Tableros**: Armado asistido, cálculo de espacios/polos, amperaje de barras y lista de materiales (*BOM*).
- [x] Maquetación de interfaz y guía visual corporativa alineada a ABV Electric Supply (`ABV-template.html` y `DESIGN.md`).

---

### Fase 2: Configuración Inicial, Repositorio y Entorno Base (Mes 2)
*Objetivo: Establecer la infraestructura de desarrollo, estándares de código y automatización de despliegue.*

Verificación local: `./scripts/check_phase2.sh --local` → **15 PASS · 0 FAIL (OPERATIVO ✅)**.

**Entregables Completados:**
- [x] Repositorio Git con estándares de commits convencionales (`feat:`, `fix:`, `chore:`) y hook `commit-msg` instalado.
- [x] Configuración segura de variables de entorno (`.env.example` versionado, `.env` ignorado en `.gitignore`, sin credenciales en repo).
- [x] Configuración de linter y formateador de alto rendimiento (`Ruff` + `pre-commit`) con 0 advertencias.
- [x] Pipeline de Integración Continua configurado en GitHub Actions (`.github/workflows/ci.yml`).
- [x] Repositorio remoto conectado (`origin` en `git@github.com:JoelJohs/electrical-cpq-system.git`).
- [x] Endpoint de diagnóstico de infraestructura operativo (`GET /health/` → `{"status": "ok"}`).
- [x] Plantillas y scripts de automatización de infraestructura para VPS en Ubuntu 24.04 LTS:
  - [x] `deploy/provision_ubuntu2404.sh` (Aprovisionamiento: UFW firewall, usuario `deployer`, dependencias del SO).
  - [x] `deploy/deploy.sh` (Despliegue automatizado, migraciones Django, recolección de estáticos y reinicio de Gunicorn).
  - [x] `deploy/setup_ssl.sh` (Generación de certificados HTTPS con Let's Encrypt y Certbot).
  - [x] `deploy/gunicorn.service` y `deploy/nginx.conf` (Systemd socket y proxy inverso seguro Nginx).
  - [x] `.github/workflows/cd.yml` (Pipeline de despliegue continuo vía SSH).
  - [x] Manual de operaciones paso a paso en `docs/deployment-vps.md`.

**Pendiente en infraestructura remota:**
- [ ] Habilitar y validar reglas de protección en rama `main` en GitHub (`./scripts/setup_branch_protection.sh`).
- [ ] Ejecutar primer ciclo de validación de CI/CD en GitHub Actions remoto.

---

### Fase 3: Arquitectura Base y Grafo de Datos (Mes 2 - Mes 3)
*Objetivo: Modelar las relaciones eléctricas en SQL garantizando integridad física y consultas de alto desempeño.*

Verificación local: `./scripts/check_phase3.sh` → **9 PASS · 0 FAIL (OPERATIVO ✅)**.  
Suite de pruebas: `uv run python manage.py test src.catalog.tests tests` → **37 PASS · 0 FAIL**.  
Linters: `uv run ruff check . && uv run ruff format --check .` → **Verde (0 errores)**.

**Entregables Completados:**
- [x] **Grafo Relacional Dirigido en SQL (`Product` y `ProductCompatibility`)**:
  - Modelado asimétrico estricto: un tablero aloja interruptores, no viceversa.
  - Tipificación formal de relaciones: `COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`.
  - Integridad en BD: `CheckConstraint` contra auto-relaciones y `UniqueConstraint` sobre tupla `(source, target, relationship_type)`.
  - Índices B-Tree compuestos sobre `(source, relationship_type)` y `(target, relationship_type)`.
  - Migraciones versionadas en `src/catalog/migrations/`.
- [x] **Infraestructura de Persistencia en Desarrollo**:
  - Contenedor PostgreSQL 17 aislado vía Docker Compose (`docker-compose.yml`).
  - Script de administración de base de datos local `scripts/db_dev.sh` (`up`, `down`, `status`, `reset`).
  - Conexión dinámica por `DATABASE_URL` con fallback automático a SQLite para tests unitarios inmediatos.
- [x] **Capa de Selectores O(1) Consultas (Sin Problema N+1)**:
  - `src/catalog/selectors.py`: Resolución del árbol completo de compatibilidad (producto base + requeridos + accesorios + alternativas) en **máximo 2 consultas SQL fijas**.
  - Validación de esquemas con Pydantic v2 en `src/catalog/schemas.py`.
- [x] **API REST con Django Ninja y OpenAPI**:
  - API modular montada en `/api/` con documentación interactiva Swagger en `/api/docs`.
  - Endpoints de catálogo: `/products/`, `/products/{id}/`, `/products/{id}/compatibilities/`, `/products/{id}/tree/`.
  - Encabezados CORS configurados con `django-cors-headers`.
- [x] **Gobernanza de Datos en Django Admin**:
  - Panel administrativo en `src/catalog/admin.py` con inlines (`ProductCompatibilityInline`) para captura ágil de reglas por personal técnico.
- [x] **Catálogo Semilla Representativo**:
  - Comando `python manage.py seed_electrical_catalog` cargando familias representativas (tablero NQ-225, interruptores QO-120 y EDB-3100, accesorios auxiliares y kit de zapatas).
  - Guía técnica en `docs/catalog-architecture.md`.

---

### Fase 4: Desarrollo del Core (Happy Path) (Mes 3 - Mes 4) 🎯 Operativo ✅
*Objetivo: Asistente interactivo de compatibilidad entre componentes y despiece de materiales en tiempo real (sin persistencia innecesaria en BD).*

Suite de pruebas: `uv run python manage.py test src.catalog.tests tests` → **37 PASS · 0 FAIL**.

**Entregables Completados:**
- [x] **Arquitectura Eficiente y Ligera (Sin Tablas Redundantes)**:
  - Enfoque directo sobre `Product` y `ProductCompatibility`.
  - Eliminación de tablas obsoletas `Quote`/`QuoteItem`: cotizaciones gestionadas en sesión viva del cliente.
- [x] **Asistente Web Interactivo (`/`)**:
  - Frontend reactivo construido con Django Templates + Tailwind CSS + Alpine.js.
  - Selector de equipo base con actualización instantánea de piezas compatibles.
  - Clasificación visual inmediata de:
    - Piezas compatibles (`COMPATIBLE_WITH`).
    - Accesorios obligatorios para instalación (`REQUIRES`).
    - Sugerencias de venta cruzada (`COMPLEMENT_OF`).
    - Alternativas de reemplazo técnico (`ALTERNATIVE_TO`).
- [x] **Lista de Materiales (BOM) en Vivo**:
  - Acumulación reactiva en memoria del navegador (sesión interactiva) con control de cantidades.
  - Función de impresión directa (`window.print()`) optimizada con estilos de impresión para taller y mostrador.
  - Cero basura residual en base de datos.
- [x] **Verificación de Tiempos de Respuesta**:
  - Consultas resueltas en milisegundos en entorno local, cumpliendo con la meta de < 2.0 segundos.

---

### Fase 5: QA, Pruebas con Casos Reales y Hardening (Mes 5)
*Objetivo: Validar la efectividad del sistema contra casos históricos reales y optimizar rendimiento.*

- [ ] **Batería de Pruebas con 30 Casos Reales de Cotización**:
  - [ ] Recopilar 30 cotizaciones y ensambles históricos reales de ABV Electric Supply (mezcla de tableros NQ, interruptores derivados, zapatas y accesorios).
  - [ ] Ejecutar los 30 casos en el sistema web y contrastar las recomendaciones contra el dictamen de ingeniería.
  - [ ] Meta de calidad: **100% de precisión técnica (0% errores de incompatibilidad física o eléctrica)**.
- [ ] **Pruebas de Rendimiento y Capacidad de Respuesta**:
  - [ ] Evaluar que el 95% de las solicitudes de compatibilidad y renderizado del árbol respondan en **menos de 2 segundos**.
  - [ ] Evaluar comportamiento bajo concurrencia simulada en servidor de pruebas.
- [ ] **Pruebas de Usabilidad e Integración Multidispositivo**:
  - [ ] Pruebas en navegadores desktop, laptops y tablets/móviles para personal de mostrador y almacén.
  - [ ] Verificación de accesibilidad básica (contraste WCAG 2.1 AA y legibilidad técnica).
- [ ] **Auditoría de Seguridad y Resiliencia**:
  - [ ] Verificación de cabeceras de seguridad, protección CSRF y validación estricta de parámetros en API Ninja.

---

### Fase 6: Despliegue en Staging, Capacitación y Reporte Final (Mes 6)
*Objetivo: Desplegar el sistema operativo, capacitar a los usuarios finales y entregar la documentación formal.*

- [ ] **Despliegue en Servidor de Pruebas (Staging / QA)**:
  - [ ] Ejecutar aprovisionamiento en VPS Ubuntu 24.04 LTS provisto por ABV (`deploy/provision_ubuntu2404.sh`).
  - [ ] Configurar Nginx con SSL Let's Encrypt (`deploy/setup_ssl.sh`) y servicio Gunicorn (`deploy/gunicorn.service`).
  - [ ] Ejecutar migraciones de producción y carga del catálogo inicial completo.
  - [ ] Validar despliegue exitoso mediante `./scripts/check_phase2.sh --remote JoelJohs/electrical-cpq-system`.
- [ ] **Capacitación y Adopción de Usuarios**:
  - [ ] Realizar sesiones de capacitación para el personal comercial (ejecutivos de mostrador y ventas externas).
  - [ ] Realizar sesiones de capacitación para el área técnica (ingenieros integradores de tableros).
  - [ ] Elaborar y entregar el **Manual de Usuario para Ventas** (búsqueda rápida, cross-selling y cotización).
  - [ ] Elaborar y entregar el **Manual de Usuario para Integradores** (reglas de ensamble, BOM e impresión).
- [ ] **Medición y Evaluación de Impacto Operativo**:
  - [ ] Medir reducción del tiempo de cotización técnica (meta: reducción del **80%**, de ~30 min a < 5 min).
  - [ ] Medir disminución de consultas rutinarias de ventas hacia ingeniería (meta: **90%** de autonomía comercial).
  - [ ] Constatar eliminación de devoluciones por incompatibilidad de piezas en casos evaluados.
- [ ] **Documentación y Cierre de Residencias Profesionales**:
  - [ ] Redacción y estructuración del Reporte Final de Residencias Profesionales conforme a lineamientos TecNM.
  - [ ] Firma de acreditación del proyecto por el Asesor Externo (Ing. Octavio Trinidad Rodríguez Ramírez - ABV).
  - [ ] Firma y aprobación del Asesor Interno / Docente del TecNM Morelia.
