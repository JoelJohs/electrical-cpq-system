# Contract: Continuous Deployment (CD) Workflow

**Interface**: GitHub Actions Automation Pipeline  
**File**: `.github/workflows/cd.yml`  
**Execution Environment**: `ubuntu-24.04` (GitHub Runner) -> Remote SSH Target (`Ubuntu 24.04 LTS VPS`)  

---

## 1. Triggers Contract

```yaml
on:
  push:
    branches:
      - main
```

El pipeline solo se dispara tras merges exitosos o pushes directos autorizados a la rama `main`.

---

## 2. Secrets & Variables Contract

El workflow requiere que los siguientes secretos existan en GitHub (Settings -> Secrets and variables -> Actions):

| Nombre del Secreto | Tipo | Obligatorio | Descripción | Ejemplo |
|--------------------|------|-------------|-------------|---------|
| `VPS_HOST` | Host / IP | Sí | Dirección IP pública o FQDN del VPS | `198.51.100.24` |
| `VPS_USER` | String | Sí | Usuario SSH con permisos sudo/deploy | `deploy` o `root` |
| `SSH_PRIVATE_KEY` | String (PEM) | Sí | Clave privada SSH sin passphrase correspondiente a la clave pública en `~/.ssh/authorized_keys` del VPS | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SSH_PORT` | Integer | No | Puerto de escucha de SSH (por defecto 22) | `22` |

---

## 3. Remote Execution Steps Contract

El pipeline debe conectarse por SSH al VPS y ejecutar la secuencia atómica definida en `/var/www/mvp-project/deploy/deploy.sh`:

1. Cambiar al directorio de la aplicación: `cd /var/www/mvp-project`
2. Actualizar rama principal: `git pull origin main`
3. Sincronizar dependencias aisladas: `/usr/local/bin/uv sync --frozen --no-dev`
4. Aplicar migraciones del esquema: `/usr/local/bin/uv run python manage.py migrate --noinput`
5. Recolectar estáticos: `/usr/local/bin/uv run python manage.py collectstatic --noinput`
6. Reiniciar servicio supervisado: `sudo systemctl restart gunicorn`
7. Validar endpoint de salud en local: `curl -fsS http://127.0.0.1:8000/health/ || curl -fsS --unix-socket /run/gunicorn.sock http://localhost/health/`

---

## 4. Error Handling & Rollback Contract

- Si el paso de `git pull`, `uv sync` o `migrate` falla, el script aborta inmediatamente gracias a `set -e`.
- El servicio `gunicorn` no se reinicia si un paso previo falló, garantizando que el proceso anterior continúe en ejecución con mínima interrupción.
- El estado del job en GitHub Actions se marca como `failure`, emitiendo alertas por correo electrónico/notificación al mantenedor.
