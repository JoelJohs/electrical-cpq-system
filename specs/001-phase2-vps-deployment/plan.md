# Implementation Plan: Cierre Operativo de Fase 2 y Despliegue en VPS Ubuntu 24.04 LTS

**Branch**: `001-phase2-vps-deployment` | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-phase2-vps-deployment/spec.md`

## Summary

Implementar y validar el cierre integral de la **Fase 2: Configuración Inicial y Repositorio** enfocado en un servidor VPS con **Ubuntu 24.04 LTS**. El plan abarca la creación del pipeline de entrega continua (CD) con GitHub Actions vía SSH, el aprovisionamiento hermético del entorno de ejecución con `uv` (Python 3.14), la configuración de `systemd` y `nginx` con certificados HTTPS (Let's Encrypt / Certbot), el establecimiento de reglas de protección sobre `main` en GitHub, y la ejecución remota satisfactoria de `scripts/check_phase2.sh` alcanzando el estado `Fase 2: EN OPERACIÓN` (0 FAIL · 0 PEND).

## Technical Context

**Language/Version**: Python >=3.14 (aprovisionado y aislado herméticamente mediante `uv`).

**Primary Dependencies**: Django >=6.1.1, Gunicorn >=26.2.0, Whitenoise >=6.12.0, django-environ >=0.14.0, Psycopg 3.3+.

**Storage**: SQLite local para la etapa MVP inicial / soporte configurable para PostgreSQL vía `dj-database-url`.

**Testing**: Ruff linter (`ruff check .`), Ruff formatter (`ruff format --check .`), Django system checks (`manage.py check`), pre-commit hooks y script de auditoría remota (`scripts/check_phase2.sh`).

**Target Platform**: Linux Server (Ubuntu 24.04 LTS), servidor web Nginx, gestor de procesos Systemd.

**Project Type**: Servicio web Django / API RESTful.

**Performance Goals**: Tiempo de respuesta en `/health/` < 2.0 segundos; ciclo completo de despliegue continuo en VPS < 60 segundos; ejecución de CI en GitHub Actions < 3 minutos.

**Constraints**:
- Entorno de ejecución aislado con `uv` sin alterar las librerías del sistema base de Ubuntu 24.04.
- Cifrado de transporte obligatorio mediante HTTPS en puerto 443 con redirección desde puerto 80.
- Secretos de entorno gestionados exclusivamente mediante `.env` en el servidor y GitHub Actions Secrets, nunca versionados en Git.
- Protección estricta de la rama `main` requiriendo checks de CI en verde para cada integración.

**Scale/Scope**: Cierre de Fase 2 de infraestructura; Hello World y monitoreo de salud operativo en producción/staging listo para el inicio de la Fase 3 (modelado de datos).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Justificación |
|-----------|--------|---------------|
| **I. Simplicidad & YAGNI** | PASS | Uso de herramientas nativas del sistema operativo (`systemd`, `nginx`, `bash`) y `uv` sin orquestadores pesados ni sobreingeniería innecesaria en esta fase. |
| **II. Automatización & Verificación** | PASS | Criterio de aceptación validado contra un script determinista (`check_phase2.sh`) y pipelines de CI/CD reproducibles. |
| **III. Seguridad & Secretos** | PASS | Variables sensibles completamente aisladas del control de versiones; cifrado TLS obligatorio de extremo a extremo. |
| **IV. Calidad & Estándares** | PASS | Commits convencionales, formateo estricto con Ruff y ejecución de checks en entornos limpios de Ubuntu 24.04. |

## Project Structure

### Documentation (this feature)

```text
specs/001-phase2-vps-deployment/
├── spec.md                  # Especificación de requerimientos y criterios de aceptación
├── plan.md                  # Este archivo (Plan de implementación técnica)
├── research.md              # Fase 0: Decisiones tecnológicas y análisis de alternativas
├── data-model.md            # Fase 1: Entidades operativas y estados de infraestructura
├── quickstart.md            # Fase 1: Guía paso a paso de aprovisionamiento y validación
├── checklists/
│   └── requirements.md      # Lista de verificación de calidad de la especificación
└── contracts/               # Fase 1: Contratos de interfaz
    ├── health-api.md        # Contrato del endpoint /health/
    ├── cd-workflow.md       # Contrato del pipeline de GitHub Actions CD
    └── vps-system-units.md  # Contrato de unidades systemd y reglas Nginx
```

### Source Code (repository root)

```text
.
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Integración continua: linters, formato y Django check
│       └── cd.yml                 # Entrega continua: despliegue automático a VPS vía SSH
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py                # Configuración Django (WhiteNoise, Allowed Hosts, Security)
│   ├── urls.py                    # Ruteo global y endpoint /health/
│   └── wsgi.py                    # Punto de entrada WSGI para Gunicorn
├── deploy/
│   ├── deploy.sh                  # Script atómico de despliegue en VPS
│   ├── gunicorn.service           # Unidad systemd para el demonio de la aplicación
│   └── nginx.conf                 # Configuración de sitio Nginx con proxy y SSL
├── docs/
│   └── basic-todo.md              # Checklist operativo por fases
├── scripts/
│   └── check_phase2.sh            # Script de verificación integral de Fase 2
├── src/
│   └── mvp_project/
├── .env.example                   # Plantilla pública de variables de entorno
├── manage.py
├── pyproject.toml                 # Metadatos del proyecto y dependencias
└── uv.lock                        # Lockfile determinista para uv
```

**Structure Decision**: Monolito modular en Django con carpeta `config/` para la aplicación central y configuraciones del framework, carpeta `deploy/` para artefactos de despliegue en el VPS Ubuntu 24.04 LTS, `.github/workflows/` para automatización CI/CD, y scripts de control de calidad en `scripts/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *Ninguna* | Arquitectura mínima y estándar | N/A |
