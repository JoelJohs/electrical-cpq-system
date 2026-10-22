# Roadmap Operativo y Checklist del Proyecto (Basic-TODO)

> **Proyecto**: Sistema Web de Selección Basado en Reglas para la Recomendación de Piezas Compatibles y Armado de Tableros Eléctricos (CPQ)  
> **Organización Receptora**: ABV ELECTRIC SUPPLY (Morelia, Michoacán)  
> **Residente**: Joel Josafat Hernández Saucedo | **Asesor Externo**: Ing. Octavio Trinidad Rodríguez Ramírez (Encargado de TI)  
> **Periodo de Ejecución**: 6 meses (01 de Agosto de 2026 – 18 de Diciembre de 2026)  
> **Especificación Global**: [`specs/003-global-cpq-roadmap/spec.md`](../specs/003-global-cpq-roadmap/spec.md)

---

## 1. Tablero General de Avance del Roadmap

| Fase / Mes | Nombre de la Fase | Enfoque Principal | Estado | Evidencia / Script de Validación |
| :---: | :--- | :--- | :---: | :--- |
| **Fase 1**<br>*(Mes 1)* | **Alineación, Alcance y Matrices** | Matriz de compatibilidad técnica, flujos comerciales/técnicos y PRD. | 🟡 En Curso | PRD de 1 página completado; pendiente validación de matrices y wireframes. |
| **Fase 2**<br>*(Mes 2)* | **Configuración Inicial y Repositorio** | Repositorio Git, CI/CD, linters Ruff, pre-commit y plantillas VPS. | 🟢 Operativo | `./scripts/check_phase2.sh --local` (15 PASS · 0 FAIL). Guía en `docs/deployment-vps.md`. |
| **Fase 3**<br>*(Mes 2-3)* | **Arquitectura Base y Grafo de Datos** | Modelado en grafo dirigido SQL, selectores O(1), API REST Ninja, Docker Postgres 17. | 🟢 Operativo | `./scripts/check_phase3.sh` (9 PASS · 0 FAIL). 25 tests en verde. Guía en `docs/catalog-architecture.md`. |
| **Fase 4**<br>*(Mes 3-4)* | **Desarrollo del Core (Happy Path)** | Asistente de compatibilidad en vivo, grafo relacional directo y lista de materiales (BOM) en memoria. | 🟢 Operativo | `./scripts/check_phase3.sh` (9 PASS · 0 FAIL). 30 tests en verde. Swagger en `/api/docs` y UI en `/`. |
| **Fase 5**<br>*(Mes 5)* | **QA, Integración y Casos Reales** | Validación funcional con **30 casos reales de cotización**, 0% errores de incompatibilidad. | ⚪ **Siguiente Paso** | Batería de pruebas con área de ingeniería y ejecutivos comerciales. |
| **Fase 6**<br>*(Mes 6)* | **Despliegue Staging y Cierre** | Despliegue en VPS Ubuntu 24.04 LTS, capacitación de usuarios y reporte final de residencia. | ⚪ Pendiente | Despliegue funcional, manuales de usuario y entrega acreditada. |

---

## 2. Detalle de Fases y Actividades Operativas

### Fase 1: Alineación, Alcance y Matrices Técnicas (Mes 1)
*Objetivo: Formalizar el conocimiento empírico de ingeniería en matrices de compatibilidad sin ambigüedades.*

- [x] Definir el problema comercial/operativo y redactar el PRD de 1 página.
- [x] Delimitar el alcance y fronteras del software (*Out of Scope*: sin e-commerce transaccional con tarjeta ni facturación CFDI/SAT en esta etapa).
- [ ] Consolidar la matriz de compatibilidades técnicas prioritarias (módulos de fuerza, protección, señalización, accesorios y envolventes/gabinetes NQ/QO/EDB).
- [ ] Definir los 2 perfiles de usuario y sus flujos de trabajo (*User Journeys*):
  1. **Ejecutivo Comercial / Ventas**: Cotización rápida asistida con recomendación inmediata de accesorios y venta cruzada (*cross-selling*).
  2. **Ingeniero Integrador de Tableros**: Armado asistido, cálculo de espacios/polos/amperaje y generación de lista de materiales (*BOM*).
- [ ] Elaborar wireframes/mockups interactivos de baja y media fidelidad (Figma) para ambos flujos.

---

### Fase 2: Configuración Inicial, Repositorio y Entorno Base (Mes 2)
*Objetivo: Establecer la infraestructura de desarrollo, estándares de código y automatización de despliegue.*

Verificación local: `./scripts/check_phase2.sh --local` → **15 PASS · 0 FAIL · 0 PEND (EN OPERACIÓN ✅)**.

**Entregables Completados:**
- [x] Repositorio Git con estándares de commits convencionales (`feat:`, `fix:`, `chore:`) y hook `commit-msg` instalado.
- [x] Configuración segura de variables de entorno (`.env.example` versionado, `.env` ignorado, sin secretos).
- [x] Configuración de linter y formateador (Ruff + pre-commit) en verde (0 errores).
- [x] Pipeline de Integración Continua configurado (`.github/workflows/ci.yml`).
- [x] Repositorio remoto conectado (`origin` en `git@github.com:JoelJohs/electrical-cpq-system.git`).
- [x] Endpoint de diagnóstico funcional en local (`GET /health/` → `{"status": "ok"}`).
- [x] Plantillas de despliegue para servidor VPS en Ubuntu 24.04 LTS:
  - `deploy/provision_ubuntu2404.sh` (Aprovisionamiento: UFW, usuario deployer, dependencias de sistema).
  - `deploy/deploy.sh` (Despliegue zero-downtime, migraciones y reinicio Gunicorn).
  - `deploy/setup_ssl.sh` (Certificados Let's Encrypt con Certbot).
  - `deploy/gunicorn.service` y `deploy/nginx.conf` (Systemd y proxy reverso HTTPS).
  - `.github/workflows/cd.yml` (Pipeline de despliegue continuo vía SSH).
  - Guía operativa paso a paso en `docs/deployment-vps.md`.

**Pendiente de ejecución en infraestructura remota:**
- [ ] Aplicar reglas de protección de rama `main` en GitHub (`./scripts/setup_branch_protection.sh`).
- [ ] Ejecutar CI remota en GitHub Actions y validar ejecución en verde.

---

### Fase 3: Arquitectura Base y Grafo de Datos (Mes 2 - Mes 3)
*Objetivo: Modelar las relaciones eléctricas en SQL garantizando integridad física y consultas de alto desempeño.*

Verificación local: `./scripts/check_phase3.sh` → **9 PASS · 0 FAIL (EN OPERACIÓN ✅)**.  
Suite de pruebas: `uv run python manage.py test` → **25 PASS · 0 FAIL**.  
Linters: `uv run ruff check . && uv run ruff format --check .` → **Verde (0 errores)**.

**Entregables Completados:**
- [x] **Grafo Dirigido en SQL (`Product` y `ProductCompatibility`)**:
  - Eliminación de la trampa del booleano bidireccional; preservación de la asimetría física (un tablero aloja un interruptor, pero el interruptor no aloja un tablero).
  - Semántica rica: `COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`.
  - Restricciones en base de datos: `prevent_self_relation` (`CheckConstraint`) y `unique_source_target_rel_type` (`UniqueConstraint`).
  - Índices compuestos B-Tree sobre `(source, relationship_type)` y `(target, relationship_type)`.
  - Migración inicial generada y aplicada (`src/catalog/migrations/0001_initial.py`).
- [x] **Infraestructura de Persistencia Desechable (Docker Compose)**:
  - Contenedor PostgreSQL 17 desechable en `docker-compose.yml` con volumen aislado.
  - Script de control `scripts/db_dev.sh` (`up`, `down`, `status`, `reset`).
  - Configuración desacoplada por `DATABASE_URL` con fallback automático a SQLite para tests unitarios.
- [x] **Capa de Selectores O(1) Consultas (Sin N+1)**:
  - `src/catalog/selectors.py`: `get_product_compatibility_tree` resuelve el árbol completo (anfitrión + derivados + accesorios) en **exactamente 2 consultas SQL fijas**.
  - Esquemas tipados con Pydantic v2 en `src/catalog/schemas.py`.
- [x] **API REST con Django Ninja y OpenAPI**:
  - API montada en `/api/` con documentación Swagger interactiva en `/api/docs`.
  - Endpoints de catálogo `/products/`, `/products/{sku}/`, `/compatibilities/`, `/tree/`.
  - CORS configurado con `django-cors-headers`.
- [x] **Gobernanza Administrativa en Django Admin**:
  - `ProductAdmin` configurado con inlines tabulares (`ProductCompatibilityInline`) para asociar productos y definir prioridades.
- [x] **Datos Semilla y Documentación de Arquitectura**:
  - Comando `python manage.py seed_electrical_catalog` cargando familias representativas (`TAB-NQ-225`, `INT-QO-120`, `INT-EDB-3100`, `ACC-AUX-QO`, `KIT-ZAP-225`).
  - Documento de referencia en `docs/catalog-architecture.md`.

---

### Fase 4: Desarrollo del Core (Happy Path) (Mes 3 - Mes 4) 🎯 Operativo ✅
*Objetivo: Asistente interactivo de compatibilidad entre componentes y despiece de materiales en tiempo real (sin persistencia de cotizaciones en BD).*

Verificación local: `./scripts/check_phase3.sh` → **9 PASS · 0 FAIL (EN OPERACIÓN ✅)**.  
Suite de pruebas: `uv run python manage.py test src.catalog.tests tests` → **30 PASS · 0 FAIL**.  
Linters: `uv run ruff check . && uv run ruff format --check .` → **Verde (0 errores)**.

**Entregables Completados:**
- [x] **Modelo Simplificado de Datos (Solo 2 Tablas en BD)**:
  - `Product`: `id` numérico convencional, `nombre_corto`, `nombre_largo`, `descripcion`, `is_active` (`src/catalog/models.py`).
  - `ProductCompatibility`: Grafo relacional dirigido (`COMPATIBLE_WITH`, `REQUIRES`, `COMPLEMENT_OF`, `ALTERNATIVE_TO`).
  - Eliminación de tablas redundantes de cotizaciones (`Quote`/`QuoteItem`), manteniendo la base de datos limpia y sin almacenar cotizaciones.
- [x] **API REST de Catálogo y Compatibilidades (Django Ninja)**:
  - Documentación Swagger interactiva en `/api/docs`.
  - Endpoints `/api/v1/catalog/products/`, `/api/v1/catalog/products/{id}/`, `/api/v1/catalog/products/{id}/compatibilities/`, `/api/v1/catalog/products/{id}/tree/`.
- [x] **Asistente Web para Clientes e Integradores (`/`)**:
  - Interfaz de autoservicio para consulta y recomendación directa con Tailwind CSS y Alpine.js.
  - Al seleccionar un equipo base, muestra instantáneamente sus componentes compatibles, accesorios obligatorios (`REQUIRES`), complementos sugeridos (`COMPLEMENT_OF`) y alternativas de reemplazo (`ALTERNATIVE_TO`).
  - Lista de Materiales (BOM) interactiva gestionada puramente en memoria del navegador (sesión en vivo).
  - Función de impresión formateada para taller y mostrador (`window.print()`).
  - Cero basura o cotizaciones guardadas en la base de datos.
- [x] **Panel de Administración**:
  - `ProductAdmin` e inlines `ProductCompatibilityInline` configurados en `src/catalog/admin.py`.

---

### Fase 5: QA, Pruebas con Casos Reales y Hardening (Mes 5)
*Objetivo: Validar la efectividad del sistema contra casos históricos reales y optimizar rendimiento.*

- [ ] **Batería de Pruebas con 30 Casos Reales**:
  - Recopilar 30 cotizaciones y ensambles históricos reales de ABV Electric Supply.
  - Ejecutar los 30 casos en el sistema y contrastar las piezas recomendadas vs. dictamen de ingeniería.
  - Meta no negociable: **100% de efectividad (0 errores de incompatibilidad física o eléctrica)**.
- [ ] **Pruebas de Rendimiento y Carga**:
  - Verificar que el 95% de las consultas de compatibilidad respondan en **menos de 2 segundos**.
  - Pruebas de estrés y límites de peticiones (*rate limiting*) para estabilidad del servidor.
- [ ] **Pruebas de Usabilidad y Diseño Responsivo**:
  - Pruebas de navegación en computadoras de escritorio y dispositivos móviles/tablets para personal en mostrador y taller.
  - Auditoría de seguridad (validación de entradas, protección contra inyecciones y CORS).

---

### Fase 6: Despliegue en Staging, Capacitación y Reporte Final (Mes 6)
*Objetivo: Desplegar el sistema operativo, capacitar a los usuarios finales y entregar la documentación formal.*

- [ ] **Despliegue en Servidor de Pruebas (Staging/QA)**:
  - Configurar servidor VPS Ubuntu 24.04 LTS con PostgreSQL, Nginx, Gunicorn y HTTPS.
  - Ejecutar migraciones y carga inicial de datos en el servidor de pruebas.
  - Verificación remota con `./scripts/check_phase2.sh --remote JoelJohs/electrical-cpq-system`.
- [ ] **Capacitación y Adopción**:
  - Capacitar al 100% del personal clave del área comercial (vendedores) y del área técnica (integradores).
  - Redactar y entregar Manuales de Usuario para Ventas y para Integradores.
- [ ] **Medición de Impacto**:
  - Medir la reducción de tiempos en el proceso de cotización (meta: reducción del **80%**, de ~30 min a < 5 min).
  - Medir la disminución de consultas rutinarias de ventas hacia ingeniería (meta: **90%** de autonomía comercial).
- [ ] **Documentación y Cierre de Residencias Profesionales**:
  - Elaboración y entrega del Reporte Final de Residencias Profesionales.
  - Acreditación formal del proyecto ante el asesor externo (ABV Electric Supply) y asesor interno (TecNM Morelia).
