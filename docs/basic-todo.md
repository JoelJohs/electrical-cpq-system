# Checklist Operativo por Fases (Basic-TODO)

## Fase 1: Alineación y Alcance

- [x] Definir el problema y redactar el PRD de 1 página.
- [ ] Listar las 3 funcionalidades no negociables que conforman el Happy Path.
- [ ] Redactar explícitamente la lista de Out of Scope.
- [ ] Crear wireframes rápidos de baja fidelidad (boceto en papel o wireframe en Figma/Excalidraw) enfocados solo en el flujo principal.

## Fase 2: Configuración Inicial y Repositorio

Verificación local: `./scripts/check_phase2.sh --local` → 13 PASS · 0 FAIL · 3 PEND.

**Completado (verificado en local):**

- [x] Inicializar el repositorio Git.
- [x] Definir estándares de commits (Conventional Commits: feat:, fix:, chore:, ...). *Verificado: hook `commit-msg` instalado, historial cumple el estándar.*
- [x] Configurar variables de entorno (.env.example versionado, secretos fuera del repo). *Verificado: `.env` ignorado, ningún secreto en el historial.*
- [x] Configurar linter y formateador de código (Ruff + pre-commit). *Verificado: `ruff check`, `ruff format --check` y `pre-commit run --all-files` en verde.*
- [x] Configurar el pipeline de CI (`.github/workflows/ci.yml`: lint, format y Django checks). *Existe y es válido, pero nunca se ha ejecutado: falta el remoto.*
- [x] Hello World funcional en local (`GET /health/` → `{"status": "ok"}`). *Verificado con servidor real levantado por el script.*

**Pendiente (requiere remoto / infraestructura):**

- [ ] Crear el remoto y subir el repositorio (`git remote add origin ...`).
- [ ] Proteger `main` (revisión obligatoria + status checks) y desarrollar en ramas de feature.
- [ ] Ejecutar la CI en GitHub y verificarla en verde sobre un PR.
- [ ] Desplegar el "Hello World" en staging/producción (Vercel, Render, Railway o VPS) para tener CI/CD automatizado desde el día 1. *Criterio: `HEALTH_URL=https://tu-app ./scripts/check_phase2.sh` en verde.*

## Fase 3: Arquitectura Base y Datos

- [ ] Diseñar y migrar el esquema inicial de base de datos (PostgreSQL, SQLite o MongoDB).
- [ ] Implementar autenticación básica (preferir proveedores gestionados como Supabase Auth, Clerk, NextAuth o Firebase para no reinventar la rueda).
- [ ] Construir la estructura de carpetas modular (separando dominio, servicios y capa de presentación/controladores).
- [ ] Validar conexiones, CORS y políticas de seguridad básicas.

## Fase 4: Desarrollo del Core (Happy Path)

- [ ] Construir el backend del flujo principal (endpoints, reglas de negocio, persistencia).
- [ ] Implementar pruebas unitarias o de integración exclusivas para la lógica crítica (ej. procesamiento de datos, cálculos o cobros).
- [ ] Construir la interfaz de usuario del flujo principal con estados de carga (loading), errores legibles y estado vacío (empty state).
- [ ] Integrar telemetría y analítica mínima (PostHog, Mixpanel o Plausible) para registrar el evento de éxito central (ej. conversion_completed).
- [ ] Configurar reporte de errores en vivo (Sentry o LogRocket).

## Fase 5: QA, Pulido y Hardening

- [ ] Realizar prueba de extremo a extremo (E2E) manual del flujo crítico en un entorno limpio (modo incógnito / cuenta nueva).
- [ ] Probar respuesta y diseño responsivo en navegadores móviles principales.
- [ ] Asegurar que los correos transaccionales críticos (si aplican) lleguen a la bandeja de entrada y no a spam.
- [ ] Verificar tiempos de carga y límites de peticiones (rate limiting básico para evitar abusos).

## Fase 6: Lanzamiento y Loop de Aprendizaje

- [ ] Desplegar versión productiva.
- [ ] Realizar onboarding guiado o pruebas presenciales con los primeros 3 a 5 usuarios reales.
- [ ] Medir la métrica de éxito contra la hipótesis inicial.
- [ ] Registrar retroalimentación cualitativa en un backlog ordenado por impacto vs. esfuerzo para la versión v1.1.
