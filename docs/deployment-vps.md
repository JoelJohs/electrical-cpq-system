# Guía Detallada de Operaciones y Despliegue en VPS (Ubuntu 24.04 LTS)

Esta guía documenta paso a paso y con nivel de detalle exhaustivo el procedimiento para aprovisionar, configurar, asegurar y desplegar la aplicación en un servidor VPS con **Ubuntu 24.04 LTS (Noble Numbat)**, incluyendo certificados SSL/TLS con Let's Encrypt y Entrega Continua (CD) mediante GitHub Actions.

---

## 1. Arquitectura del Entorno de Producción

```text
[ Internet / Cliente ]
          │ (HTTPS : 443 / HTTP : 80 con redirección 301)
          ▼
   [ Nginx Reverse Proxy ]
          │
          ├──> /static/ ──> Servido directo desde /var/www/mvp-project/staticfiles/ (Caché inmutable)
          ├──> /media/  ──> Servido directo desde /var/www/mvp-project/media/
          │
          └──> / y demás rutas (ej. /health/)
                    │ (Unix Domain Socket: /run/gunicorn.sock)
                    ▼
          [ Gunicorn WSGI Daemon ] (Supervisado por systemd con auto-restart)
                    │
          [ uv run config.wsgi:application ] (CPython 3.14 hermético y aislado)
                    │
              [ Django Core ]
```

---

## 2. Prerrequisitos y Preparación Previa

Antes de comenzar la instalación en el VPS, asegúrate de contar con:

1. **Instancia VPS activa con Ubuntu 24.04 LTS**:
   - Acceso con dirección IP pública (ej. `203.0.113.10`).
   - Acceso inicial vía SSH como `root`.

2. **Dominio DNS configurado**:
   - En tu proveedor de DNS (Cloudflare, Namecheap, GoDaddy, etc.), crea los siguientes registros tipo **A**:
     - `tu-dominio.com` ➔ `203.0.113.10`
     - `www.tu-dominio.com` ➔ `203.0.113.10` (opcional o registro CNAME)
   - *Nota*: Espera unos minutos hasta que la resolución DNS responda (`ping tu-dominio.com`).

3. **Creación de usuario de despliegue (`deploy`) en el VPS**:
   Se recomienda no ejecutar la aplicación ni los despliegues como `root`.
   ```bash
   # Conectado como root en el VPS:
   adduser deploy
   usermod -aG sudo deploy

   # Permitir al usuario deploy reiniciar Gunicorn sin contraseña para el CD automatizado:
   echo "deploy ALL=(ALL) NOPASSWD: /bin/systemctl restart gunicorn" | tee /etc/sudoers.d/deploy-gunicorn
   chmod 440 /etc/sudoers.d/deploy-gunicorn
   ```

4. **Configurar acceso SSH para el usuario `deploy`**:
   Desde tu máquina de desarrollo local:
   ```bash
   # Copiar tu llave pública local al usuario deploy del VPS:
   ssh-copy-id deploy@<IP_VPS>
   ```

---

## 3. Aprovisionamiento Automatizado del VPS

Conéctate al VPS como el usuario `deploy`:
```bash
ssh deploy@<IP_VPS>
```

### Paso 3.1: Descargar el repositorio y ejecutar el aprovisionador
```bash
# 1. Crear directorio base con permisos adecuados
sudo mkdir -p /var/www/mvp-project
sudo chown -R deploy:www-data /var/www/mvp-project
sudo chmod -R 775 /var/www/mvp-project

# 2. Clonar el repositorio oficial
git clone https://github.com/JoelJohs/electrical-cpq-system.git /var/www/mvp-project
cd /var/www/mvp-project

# 3. Ejecutar el script de aprovisionamiento base
sudo ./deploy/provision_ubuntu2404.sh
```

**¿Qué hace automáticamente `provision_ubuntu2404.sh`?**
- Actualiza índices de APT (`apt-get update && apt-get upgrade -y`).
- Instala herramientas del sistema: `git`, `curl`, `nginx`, `certbot`, `python3-certbot-nginx`, `build-essential`, `libpq-dev`, `ufw`.
- Instala el gestor de paquetes de alto rendimiento `uv` y asegura el binario universal en `/usr/local/bin/uv`.
- Configura el Firewall UFW permitiendo solo puertos esenciales (`OpenSSH` y `Nginx Full`: 80 y 443).
- Prepara los directorios de estáticos, media y logs (`/var/log/gunicorn`).

---

## 4. Configuración del Entorno de Producción (`.env`)

Dentro del VPS, crea el archivo de configuración sensible fuera del control de versiones:

```bash
cd /var/www/mvp-project
cp deploy/.env.production.example .env
chmod 600 .env
```

### Paso 4.1: Generar clave secreta y editar `.env`
Genera una clave criptográfica aleatoria con `uv`:
```bash
/usr/local/bin/uv run python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Edita el archivo `.env`:
```bash
nano .env
```

Configura los valores reales:
```ini
# Pega aquí la clave generada
SECRET_KEY="tu-clave-secreta-generada-super-segura"

# SIEMPRE en False para entornos de producción
DEBUG=False

# Dominios autorizados separados por comas
ALLOWED_HOSTS="tu-dominio.com,www.tu-dominio.com,127.0.0.1,localhost"

# Orígenes confiables para validación CSRF sobre HTTPS
CSRF_TRUSTED_ORIGINS="https://tu-dominio.com,https://www.tu-dominio.com"

# Base de datos SQLite inicial (o PostgreSQL si aplica)
DATABASE_URL="sqlite:////var/www/mvp-project/db.sqlite3"
```

Guarda los cambios con `Ctrl + O`, `Enter` y sal con `Ctrl + X`.

---

## 5. Instalación de Dependencias, Migraciones y Archivos Estáticos

Ejecuta la primera preparación del runtime:

```bash
cd /var/www/mvp-project

# 1. Sincronizar dependencias herméticas con uv (descarga Python 3.14 y las librerías a .venv)
/usr/local/bin/uv sync --frozen --no-dev

# 2. Comprobar seguridad y configuración de Django
/usr/local/bin/uv run python manage.py check --deploy

# 3. Aplicar migraciones iniciales de la base de datos
/usr/local/bin/uv run python manage.py migrate --noinput

# 4. Recolectar archivos estáticos para que Nginx pueda servirlos
/usr/local/bin/uv run python manage.py collectstatic --noinput

# 5. Asegurar permisos para el grupo www-data (necesario para lectura de estáticos y escritura en db.sqlite3)
sudo chown -R deploy:www-data /var/www/mvp-project
sudo chmod -R 775 /var/www/mvp-project/staticfiles
sudo chmod 664 /var/www/mvp-project/db.sqlite3 2>/dev/null || true
```

---

## 6. Configuración del Demonio Gunicorn con Systemd

1. **Instalar el archivo de servicio systemd**:
   ```bash
   sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn.service
   ```

2. **Recargar systemd y activar el servicio**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now gunicorn
   ```

3. **Verificar que Gunicorn esté activo**:
   ```bash
   sudo systemctl status gunicorn
   ```
   Debe mostrar `Active: active (running)`.

4. **Verificar creación del socket Unix**:
   ```bash
   ls -la /run/gunicorn.sock
   ```
   El socket debe existir con permisos para `www-data`.

---

## 7. Configuración de Nginx y Certificados SSL/TLS (Let's Encrypt)

### Paso 7.1: Instalar y habilitar el sitio en Nginx
```bash
# 1. Copiar la plantilla de configuración a sites-available
sudo cp deploy/nginx.conf /etc/nginx/sites-available/mvp-project

# 2. Configurar tu dominio real en la directiva server_name
sudo sed -i 's/tu-dominio.com www.tu-dominio.com/tu-dominio.com/g' /etc/nginx/sites-available/mvp-project

# 3. Habilitar el sitio mediante enlace simbólico
sudo ln -sf /etc/nginx/sites-available/mvp-project /etc/nginx/sites-enabled/

# 4. Deshabilitar el sitio por defecto de Nginx si existe
sudo rm -f /etc/nginx/sites-enabled/default

# 5. Probar la sintaxis de Nginx y recargar
sudo nginx -t
sudo systemctl restart nginx
```

### Paso 7.2: Emitir certificado SSL con Certbot (HTTPS)
Ejecuta el script automatizado indicando tu dominio y tu correo para notificaciones de Let's Encrypt:

```bash
sudo ./deploy/setup_ssl.sh tu-dominio.com tu-email@dominio.com
```

**¿Qué hace este paso?**
- Solicita el certificado a Let's Encrypt para `tu-dominio.com`.
- Modifica la configuración de Nginx para abrir el puerto `443` con cifrado TLS.
- Configura una redirección permanente (HTTP 301) desde el puerto `80` hacia `443`.
- Activa el temporizador de systemd (`certbot.timer`) para renovar los certificados automáticamente antes de que expiren.

### Paso 7.3: Comprobar endpoint de salud
Desde el mismo VPS o tu navegador:
```bash
curl -i https://tu-dominio.com/health/
```
**Respuesta esperada**:
```http
HTTP/2 200 
content-type: application/json
...
{"status": "ok"}
```

---

## 8. Automatización de Entrega Continua (CD) con GitHub Actions

Para que cada cambio fusionado a la rama `main` se despliegue automáticamente en el VPS:

### Paso 8.1: Generar clave SSH dedicada para despliegues
En tu máquina local:
```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key -N ""
```
Esto genera dos archivos:
- `~/.ssh/github_deploy_key` (clave privada)
- `~/.ssh/github_deploy_key.pub` (clave pública)

### Paso 8.2: Autorizar la clave pública en el VPS
Copia el contenido de `~/.ssh/github_deploy_key.pub` y agrégalo en el VPS:
```bash
# En el VPS como usuario deploy:
mkdir -p ~/.ssh && chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Pega la clave pública al final del archivo y guarda
chmod 600 ~/.ssh/authorized_keys
```

### Paso 8.3: Configurar Secretos en GitHub
Ve a tu repositorio en GitHub:
**Settings ➔ Secrets and variables ➔ Actions ➔ New repository secret**

Agrega los siguientes 4 secretos:

| Secreto | Valor | Ejemplo |
|---------|-------|---------|
| `VPS_HOST` | Dirección IP pública o nombre de dominio del VPS | `203.0.113.10` |
| `VPS_USER` | Usuario SSH configurado | `deploy` |
| `SSH_PRIVATE_KEY` | Contenido completo de `~/.ssh/github_deploy_key` (incluyendo `-----BEGIN` y `-----END`) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SSH_PORT` | Puerto de escucha SSH | `22` |

A partir de este momento, cada vez que hagas `git push origin main` o fusiones un Pull Request, el workflow [`.github/workflows/cd.yml`](file:///home/jojo/mvp-project/.github/workflows/cd.yml) se conectará vía SSH y ejecutará `/var/www/mvp-project/deploy/deploy.sh`.

---

## 9. Protección de la Rama `main` en GitHub

Para garantizar que nadie pueda subir cambios directos sin pasar por validaciones de CI:

```bash
# Desde tu máquina local, inicia sesión en GitHub CLI si no lo has hecho:
gh auth login

# Ejecutar el script que configura la protección de la rama:
./scripts/setup_branch_protection.sh JoelJohs/electrical-cpq-system
```

Reglas aplicadas:
- Requiere Pull Request para integrar código en `main`.
- Exige que el status check `lint-and-test` (de `.github/workflows/ci.yml`) esté en verde.
- No bloquea al desarrollador individual con revisiones obligatorias de terceros (0 approvals requeridas).

---

## 10. Verificación Final de la Fase 2

Para certificar que la infraestructura remota cumple el 100% de los criterios operativos de la Fase 2:

```bash
HEALTH_URL=https://tu-dominio.com ./scripts/check_phase2.sh --remote JoelJohs/electrical-cpq-system
```

**Resultado esperado**:
```text
════════════════════════════════════════════════════════════════
Resultado: 16 PASS · 0 FAIL · 0 WARN · 0 PEND
Fase 2: EN OPERACIÓN ✅
════════════════════════════════════════════════════════════════
```

---

## 11. Diagnóstico y Solución de Problemas (Troubleshooting)

### Error 502 Bad Gateway
- **Causa**: Nginx está corriendo pero no puede comunicarse con Gunicorn a través del socket Unix.
- **Diagnóstico**:
  ```bash
  sudo systemctl status gunicorn
  sudo journalctl -u gunicorn -n 50 --no-pager
  ls -la /run/gunicorn.sock
  ```
- **Solución**: Revisa si Gunicorn falló por algún error de sintaxis en `config/settings.py` o si los permisos del archivo `/run/gunicorn.sock` no permiten el acceso al usuario `www-data`.

### Error 400 Bad Request
- **Causa**: Petición recibida con una cabecera `Host` no listada en `ALLOWED_HOSTS`.
- **Solución**: Asegúrate de que el dominio con el que accedes esté incluido exactamente en `ALLOWED_HOSTS` dentro de `/var/www/mvp-project/.env`.

### Error de CSRF Verification Failed
- **Causa**: Falta el esquema completo del dominio en `CSRF_TRUSTED_ORIGINS`.
- **Solución**: Agrega `https://tu-dominio.com` en `CSRF_TRUSTED_ORIGINS` dentro de `.env`.

### Monitoreo de Logs en Vivo
- **Logs de Nginx (errores de proxy)**:
  ```bash
  sudo tail -f /var/log/nginx/error.log
  ```
- **Logs de Nginx (tráfico de accesos)**:
  ```bash
  sudo tail -f /var/log/nginx/access.log
  ```
- **Logs de Gunicorn / Django**:
  ```bash
  sudo journalctl -u gunicorn -f
  ```
