# Research & Technical Decisions: Cierre Operativo Fase 2 (VPS Ubuntu 24.04 LTS)

**Feature**: `001-phase2-vps-deployment`  
**Date**: 2026-10-18  
**Status**: Completed  

---

## 1. Despliegue Continuo (CD) automatizado vía GitHub Actions y SSH

### Contexto
El requerimiento funcional FR-004 establece que cada fusión o push a la rama `main` debe desplegarse automáticamente al VPS con Ubuntu 24.04 LTS sin intervención manual, garantizando la trazabilidad y la inmediatez de las actualizaciones.

### Decisión
Implementar un workflow de GitHub Actions (`.github/workflows/cd.yml`) activado en `push` a la rama `main` que utilice la acción probada `appleboy/ssh-action@v1.2.0` (o conexión SSH autenticada por clave privada) para invocar el script `/var/www/mvp-project/deploy/deploy.sh` en el VPS.

### Racional
- **Idempotencia y simplicidad**: El repositorio ya cuenta con `deploy/deploy.sh`, el cual orquesta:
  1. `git pull origin main`
  2. `uv sync --frozen --no-dev`
  3. `uv run python manage.py migrate --noinput`
  4. `uv run python manage.py collectstatic --noinput`
  5. `sudo systemctl restart gunicorn`
- **Aislamiento de credenciales**: Se utilizan GitHub Actions Secrets (`VPS_HOST`, `VPS_USER`, `SSH_PRIVATE_KEY`, `SSH_PORT`) sin almacenar claves en texto plano.
- **Fail-fast**: Si cualquier comando falla (`set -e`), el workflow se detiene y marca el run como fallido, alertando al desarrollador.

### Alternativas Consideradas
- **Webhook HTTP custom en el VPS**: Requiere mantener un proceso demonio escuchando en un puerto adicional en el VPS y verificar firmas HMAC de GitHub. Añade superficie de ataque y puntos de fallo innecesarios.
- **Pull manual vía SSH**: Descartado por no cumplir el requerimiento de automatización continua (FR-004).
- **Contenedores Docker / Docker Compose**: Añade capas de sobrecarga y complejidad innecesarias para un MVP monolitico en Django con base de datos SQLite/Postgres local en Fase 2.

---

## 2. Aprovisionamiento y Runtime Python 3.14 en Ubuntu 24.04 LTS con `uv`

### Contexto
Ubuntu 24.04 LTS (Noble Numbat) incluye Python 3.12 en sus repositorios APT oficiales. No obstante, el proyecto requiere `Python >=3.14` según `pyproject.toml` y `.python-version`.

### Decisión
Utilizar el instalador oficial y standalone de `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`) en el servidor VPS. `uv` se encarga de descargar, compilar o aprovisionar el binario hermético de CPython 3.14 en el directorio de usuario (ej. `/root/.local/share/uv/python` o `/home/deploy/.local/share/uv/python`) y construir el entorno virtual `.venv` aislado con las dependencias fijadas en `uv.lock`.

### Racional
- Elimina la necesidad de compilar Python manualmente desde fuentes o añadir PPAs de terceros no oficiales (como deadsnakes) que pueden tener retrasos con versiones recientes de Python.
- Coherencia absoluta entre el entorno local de desarrollo y el VPS de producción: ambos usan la misma versión exacta del lockfile y el mismo manejador de paquetes (`uv`).

### Ajuste de Configuración Systemd
- Ubicar el binario `uv` en `/usr/local/bin/uv` (o crear un enlace simbólico desde `~/.local/bin/uv` hacia `/usr/local/bin/uv`) para que el servicio systemd `gunicorn.service` pueda ejecutarlo de forma universal y confiable independientemente del usuario del proceso.
- En `gunicorn.service`, asegurar la directiva `ExecStart=/usr/local/bin/uv run gunicorn config.wsgi:application --workers 3 --bind unix:/run/gunicorn.sock`.

---

## 3. Reverse Proxy Nginx y Certificados SSL/TLS (Let's Encrypt / Certbot)

### Contexto
El requerimiento FR-005 exige que el servidor responda obligatoriamente con HTTPS y certificado SSL/TLS válido para el dominio del proyecto.

### Decisión
- Instalar Nginx en Ubuntu 24.04 LTS (`apt install nginx`).
- Configurar el bloque de servidor en `/etc/nginx/sites-available/mvp-project` enlazado a `sites-enabled`.
- Instalar Certbot mediante paquetes oficiales (`apt install certbot python3-certbot-nginx`).
- Ejecutar `certbot --nginx -d <dominio> --non-interactive --agree-tos -m <email> --redirect` para emitir el certificado y configurar la redirección automática HTTP (puerto 80) -> HTTPS (puerto 443).
- Systemd de Ubuntu 24.04 incluye un temporizador nativo `certbot.timer` que renueva automáticamente los certificados antes de su expiración.

### Alternativas Consideradas
- **Caddy**: Automatiza TLS pero difiere de la configuración ya avanzada en `deploy/nginx.conf`. Mantener Nginx aprovecha el trabajo previo y es el estándar de referencia en despliegues Django.
- **SSL solo en Cloudflare (Flexible)**: Deja el tráfico entre Cloudflare y el VPS sin cifrar; no cumple con el estándar de cifrado extremo a extremo.

---

## 4. Gobernanza y Protección de Rama `main` en GitHub

### Contexto
El requerimiento FR-006 define que la rama `main` debe quedar protegida exigiendo status checks de CI en verde antes de permitir fusiones, pero sin bloquear el flujo unipersonal con revisiones externas obligatorias.

### Decisión
Configurar Branch Protection Rule en GitHub sobre la rama `main` del repositorio `JoelJohs/electrical-cpq-system`:
- **Require a pull request before merging**: habilitado.
- **Require approvals**: 0 (o desmarcado "Require approvals" para no bloquear merges de un único autor).
- **Require status checks to pass before merging**: habilitado.
- **Status check obligatorio**: `lint-and-test` (definido en `.github/workflows/ci.yml`).
- **Do not allow bypassing the above settings**: habilitado (o restringido a administradores con trazabilidad).

### Racional
Garantiza que ningún cambio ingrese a `main` sin pasar por un Pull Request verificado por Ruff, linters y los chequeos del framework Django, satisfaciendo el estándar de desarrollo profesional sin fricción para el desarrollador individual.

---

## 5. Criterio de Verificación Automatizada con `scripts/check_phase2.sh`

### Contexto
El cierre de la Fase 2 exige que `./scripts/check_phase2.sh` reporte `0 FAIL` y `0 PEND` ("Fase 2: EN OPERACIÓN").

### Decisión
El checklist remoto evalúa:
1. `git rev-parse --git-dir` -> PASS (repositorio inicializado).
2. `git remote` -> PASS (`origin` configurado).
3. Ramas além de `main` -> PASS (ramas de feature existentes).
4. Protección de `main` -> PASS (verificado con `gh api repos/JoelJohs/electrical-cpq-system/branches/main/protection` o reglas de ruleset).
5. Commits convencionales -> PASS (todos los commits siguen `feat:`, `fix:`, `chore:`, etc.).
6. Secretos y `.env` -> PASS (`.env.example` en repo, `.env` fuera del repo).
7. Ruff y pre-commit -> PASS.
8. CI en GitHub -> PASS (última corrida `completed/success`).
9. Health check en vivo -> PASS (`curl -fsS "$HEALTH_URL/health/"` responde `{"status": "ok"}`).

Todas las condiciones quedan cubiertas y planificadas sin dependencias pendientes.
