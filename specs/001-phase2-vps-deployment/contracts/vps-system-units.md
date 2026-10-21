# Contract: VPS System Units & Service Definitions

**Platform**: Ubuntu 24.04 LTS  
**Components**: `systemd`, `nginx`, `certbot`, `uv`  

---

## 1. Systemd Service Unit Contract (`gunicorn.service`)

**Target Path**: `/etc/systemd/system/gunicorn.service`  

### Contract Specifications
- **User**: `www-data` (o usuario del grupo web)
- **Group**: `www-data`
- **WorkingDirectory**: `/var/www/mvp-project`
- **ExecStart**: `/usr/local/bin/uv run gunicorn config.wsgi:application --workers 3 --bind unix:/run/gunicorn.sock --access-logfile - --error-logfile -`
- **Restart**: `always`
- **RestartSec**: `5`
- **Socket Perms**: Socket `/run/gunicorn.sock` debe ser accesible y tener permisos de lectura/escritura para `www-data`.

---

## 2. Nginx Virtual Host Contract (`mvp-project`)

**Target Path**: `/etc/nginx/sites-available/mvp-project`  
**Symlink**: `/etc/nginx/sites-enabled/mvp-project`  

### Routing Rules Contract
1. **HTTP (Port 80)**:
   - Toda petición HTTP debe ser redirigida automáticamente con código HTTP 301 a `https://$host$request_uri` (gestionado por Certbot).
   - Rutas `.well-known/acme-challenge/` deben responder en HTTP para validaciones de certificados ACME.
2. **HTTPS (Port 443)**:
   - **`/static/`**: Mapeado directamente a alias `/var/www/mvp-project/staticfiles/` con cabeceras `Cache-Control "public, max-age=2592000"`.
   - **`/media/`**: Mapeado directamente a alias `/var/www/mvp-project/media/`.
   - **`/` y demás rutas (incluyendo `/health/`)**: Proxy inverso a `http://unix:/run/gunicorn.sock` con cabeceras de proxy (`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`).
