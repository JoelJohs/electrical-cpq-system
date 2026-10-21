# Tasks: Cierre Operativo de Fase 2 y Despliegue en VPS Ubuntu 24.04 LTS

**Feature**: `001-phase2-vps-deployment`  
**Input**: Plan from `specs/001-phase2-vps-deployment/plan.md`  
**Spec**: `specs/001-phase2-vps-deployment/spec.md`  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparación de plantillas, scripts base de despliegue y configuraciones de servicios para el VPS Ubuntu 24.04 LTS.

- [X] T001 Crear plantilla de variables de entorno de producción en deploy/.env.production.example definiendo SECRET_KEY, DEBUG=False, ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS
- [X] T002 [P] Actualizar configuración de la unidad systemd en deploy/gunicorn.service fijando la ruta de uv en /usr/local/bin/uv y permisos sobre el socket /run/gunicorn.sock
- [X] T003 [P] Actualizar configuración del proxy inverso en deploy/nginx.conf con directivas de cabeceras seguras, soporte de alias estáticos y redirección HTTPS
- [X] T004 [P] Robustecer el script de despliegue en deploy/deploy.sh incluyendo validación de precondiciones, sincronización congelada con uv sync --frozen y reinicio seguro del demonio

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura central y pruebas de contrato que DEBEN completarse antes de iniciar el despliegue de las historias de usuario.

**⚠️ CRITICAL**: Ningún despliegue o verificación remota puede completarse sin estas tareas base.

- [X] T005 Ajustar directivas de producción en config/settings.py para soportar cabeceras proxy X-Forwarded-Proto, STATIC_ROOT y variables de entorno con django-environ
- [X] T006 [P] Crear script de aprovisionamiento automatizado del VPS en deploy/provision_ubuntu2404.sh para instalar dependencias de sistema (nginx, certbot, uv, git), crear directorios y configurar permisos www-data
- [X] T007 [P] Crear prueba de integración y contrato del endpoint de salud en tests/integration/test_health.py validando retorno HTTP 200 y cuerpo JSON {"status": "ok"}

**Checkpoint**: Base técnica lista: scripts de aprovisionamiento, servicio WSGI y pruebas base preparadas.

---

## Phase 3: User Story 1 - Despliegue y Verificación de Disponibilidad en VPS (Priority: P1) 🎯 MVP

**Goal**: Desplegar la aplicación en un servidor VPS con Ubuntu 24.04 LTS, configurar Nginx con HTTPS (Let's Encrypt), supervisar Gunicorn con systemd y habilitar el pipeline CD con GitHub Actions.

**Independent Test**: Realizar una petición HTTPS al endpoint `/health/` (`curl -fsS https://<dominio>/health/`) y verificar respuesta HTTP 200 con JSON `{"status": "ok"}` en menos de 2.0 segundos.

### Tests for User Story 1 ⚠️

- [X] T008 [P] [US1] Crear prueba unitaria de la vista de monitoreo de salud en tests/unit/test_health_view.py verificando cabeceras y estructura JSON

### Implementation for User Story 1

- [X] T009 [P] [US1] Crear script de emisión y renovación de certificados TLS en deploy/setup_ssl.sh utilizando Certbot con plugin de Nginx
- [X] T010 [US1] Crear pipeline de Entrega Continua (CD) en .github/workflows/cd.yml para automatizar el despliegue al VPS vía SSH ante pushes a la rama main
- [ ] T011 [US1] Ejecutar aprovisionamiento del VPS Ubuntu 24.04 LTS mediante deploy/provision_ubuntu2404.sh y deploy/setup_ssl.sh en el servidor remoto
- [ ] T012 [US1] Realizar el despliegue inicial en el VPS y verificar disponibilidad del socket WSGI y del endpoint seguro en https://<dominio>/health/

**Checkpoint**: User Story 1 (MVP) completada: aplicación corriendo en VPS Ubuntu 24.04 LTS bajo HTTPS con despliegue continuo automatizado.

---

## Phase 4: User Story 2 - Integración Continua y Validación Automática de Calidad (Priority: P2)

**Goal**: Garantizar que cada Pull Request y push ejecute automáticamente el pipeline de CI en GitHub Actions, impidiendo que código con errores de linters, formateo o pruebas llegue a `main`.

**Independent Test**: Subir una rama de feature (`feat/...`), abrir un Pull Request en GitHub y comprobar que el workflow de CI ejecute y reporte éxito (`completed/success`) en verde.

### Implementation for User Story 2

- [X] T013 [P] [US2] Actualizar el pipeline de CI en .github/workflows/ci.yml agregando la ejecución de pruebas automatizadas con uv run python -m unittest o pytest junto a Ruff y comprobaciones de Django
- [ ] T014 [US2] Crear una rama de funcionalidad de prueba feat/verify-ci en Git, abrir Pull Request en GitHub y validar ejecución exitosa en verde del check lint-and-test

**Checkpoint**: User Story 2 completada: pipeline de CI validado sobre Pull Requests reales en el repositorio remoto.

---

## Phase 5: User Story 3 - Protección de Rama Principal y Flujo de Entrega (Priority: P3)

**Goal**: Configurar reglas de protección de rama sobre `main` en GitHub para exigir checks de CI en verde antes del merge y prohibir pushes directos descontrolados.

**Independent Test**: Verificar que un intento de push directo a `main` sea rechazado por el repositorio remoto y que la fusión de PRs solo se autorice cuando el check `lint-and-test` haya completado exitosamente sin requerir aprobación externa.

### Implementation for User Story 3

- [X] T015 [P] [US3] Crear script de configuración de reglas de protección en scripts/setup_branch_protection.sh utilizando gh api para aplicar status check obligatorio lint-and-test y 0 aprobaciones requeridas
- [ ] T016 [US3] Ejecutar la configuración de branch protection en el repositorio remoto JoelJohs/electrical-cpq-system aplicando las reglas sobre la rama main
- [ ] T017 [US3] Validar rechazo de push directo a main en Git y habilitación de merge tras superación del check en GitHub

**Checkpoint**: User Story 3 completada: gobernanza de rama `main` activa y verificable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentación operativa, actualización de checklists y verificación remota final para cerrar la Fase 2.

- [X] T018 [P] Documentar el procedimiento operativo de aprovisionamiento, despliegue y mantenimiento del VPS en docs/deployment-vps.md
- [X] T019 [P] Actualizar el checklist operativo en docs/basic-todo.md marcando los 4 ítems de infraestructura de la Fase 2 como completados
- [ ] T020 Ejecutar la auditoría final remota ejecutando HEALTH_URL=https://<dominio> ./scripts/check_phase2.sh --remote JoelJohs/electrical-cpq-system y verificar resultado 0 FAIL y 0 PEND

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
[T008-T012] 🎯 MVP         [T013-T014]             [T015-T017]
     │                       │                       │
     └───────────────────────┴───────────────────────┘
                             │
                             ▼
              Phase 6: Polish & Verification (T018-T020)
```

### User Story Dependencies

- **User Story 1 (P1)**: Requiere Fase 1 y Fase 2 completadas. No depende de US2 ni de US3.
- **User Story 2 (P2)**: Requiere Fase 2 completada (pruebas base existentes en T007).
- **User Story 3 (P3)**: Requiere que el check `lint-and-test` de US2 esté definido para poder registrarlo como obligatorio en GitHub.
- **Polish (Fase 6)**: Requiere que US1, US2 y US3 estén implementadas para validar el script de cierre integral en T020.

---

## Parallel Opportunities

- **Fase 1 (Setup)**: T002, T003 y T004 pueden ejecutarse en paralelo (archivos independientes: `gunicorn.service`, `nginx.conf`, `deploy.sh`).
- **Fase 2 (Foundational)**: T006 (`provision_ubuntu2404.sh`) y T007 (`test_health.py`) pueden desarrollarse en paralelo.
- **Historias de Usuario**: Una vez concluida la Fase 2, T008/T009 (US1) y T013 (US2) pueden iniciarse simultáneamente.
- **Fase 6 (Polish)**: T018 (`docs/deployment-vps.md`) y T019 (`docs/basic-todo.md`) pueden prepararse en paralelo antes de la validación final T020.

---

## Parallel Example: User Story 1 & 2

```bash
# Desarrollar en paralelo componentes independientes:
Task: "T008 [P] [US1] Crear prueba unitaria de la vista de monitoreo de salud en tests/unit/test_health_view.py"
Task: "T009 [P] [US1] Crear script de emisión y renovación de certificados TLS en deploy/setup_ssl.sh"
Task: "T013 [P] [US2] Actualizar el pipeline de CI en .github/workflows/ci.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Completar Fase 1 (Setup) y Fase 2 (Foundational).
2. Implementar Fase 3 (User Story 1): Aprovisionar VPS Ubuntu 24.04 LTS, configurar Nginx/SSL, supervisar Gunicorn y configurar pipeline CD.
3. **Punto de Control MVP**: Probar `curl -fsS https://<dominio>/health/`. Si responde HTTP 200 `{"status": "ok"}`, el entorno de producción remoto está vivo y validado.

### Incremental Delivery

1. **Incremento 1 (MVP)**: VPS activo y respondiendo a peticiones con HTTPS y despliegue continuo (US1).
2. **Incremento 2 (Calidad Automática)**: CI ejecutando en GitHub Actions en cada PR (US2).
3. **Incremento 3 (Gobernanza)**: Rama `main` blindada con reglas de protección en GitHub (US3).
4. **Cierre Definitivo**: Ejecución de `scripts/check_phase2.sh` reportando `Fase 2: EN OPERACIÓN` (0 FAIL · 0 PEND) y documentación actualizada.
