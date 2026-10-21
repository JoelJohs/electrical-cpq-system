# Quickstart: Guía de Validación y Cierre Operativo de Fase 2

**Feature**: `001-phase2-vps-deployment`  
**Objetivo**: Validar el despliegue en un VPS con Ubuntu 24.04 LTS y verificar que `./scripts/check_phase2.sh` reporte `0 FAIL · 0 PEND` ("Fase 2: EN OPERACIÓN").

---

## Prerrequisitos

1. **Instancia VPS activa**:
   - Ubuntu 24.04 LTS (Noble Numbat).
   - Acceso SSH con clave pública y privilegios `sudo`.
   - Dirección IP pública accesible en internet.
2. **Dominio DNS**:
   - Nombre de dominio apuntando con registro tipo `A` a la IP pública del VPS (ej. `app.tu-dominio.com` -> `IP_VPS`).
3. **Repositorio GitHub**:
   - Repositorio remoto configurado en `JoelJohs/electrical-cpq-system`.
   - Secretos de GitHub Actions configurados (`VPS_HOST`, `VPS_USER`, `SSH_PRIVATE_KEY`, `SSH_PORT`).

---

## Escenarios de Validación Paso a Paso

### Escenario 1: Validación Local Previa
Verificar que la base de código local cumple todos los estándares antes de subir cambios.

```bash
# 1. Comprobar linters y pre-commit en local
uv run ruff check .
uv run ruff format --check .
uv run pre-commit run --all-files

# 2. Comprobar verificación local de Fase 2
./scripts/check_phase2.sh --local
```
**Resultado esperado**:
- Ruff y pre-commit en verde sin errores.
- Script reporta `13 PASS · 0 FAIL · 0 WARN · 3 PEND` ("Fase 2 (modo local): LOCALMENTE LISTA").

---

### Escenario 2: Validación del Pipeline de CI en Pull Request
Comprobar que el flujo de ramas y CI en GitHub protege la rama `main`.

```bash
# 1. Crear rama de feature y subir cambio
git checkout -b feat/phase2-vps-cd
# (Realizar commits convencionales, ej. 'feat: add cd workflow for vps')
git push -u origin feat/phase2-vps-cd

# 2. Abrir Pull Request hacia main
# Verificar en GitHub Actions que el workflow 'CI Pipeline' (job lint-and-test) corra y termine en verde
```
**Resultado esperado**:
- El check `lint-and-test` se ejecuta en Ubuntu 24.04 y finaliza con `success`.
- GitHub autoriza la fusión (merge) hacia `main`.

---

### Escenario 3: Aprovisionamiento y Despliegue en el VPS Ubuntu 24.04 LTS
Aprovisionar el servidor y desplegar la versión inicial en `/var/www/mvp-project`.

```bash
# Conectarse al VPS por SSH
ssh usuario@<IP_VPS>

# 1. Instalar paquetes base en Ubuntu 24.04 LTS
sudo apt update && sudo apt install -y git curl nginx certbot python3-certbot-nginx

# 2. Instalar uv hermético
curl -LsSf https://astral.sh/uv/install.sh | sh
sudo cp ~/.local/bin/uv /usr/local/bin/uv

# 3. Clonar repositorio y configurar permisos
sudo mkdir -p /var/www/mvp-project
sudo chown -R $USER:www-data /var/www/mvp-project
git clone git@github.com:JoelJohs/electrical-cpq-system.git /var/www/mvp-project
cd /var/www/mvp-project

# 4. Crear archivo .env de producción
cp .env.example .env
# Configurar SECRET_KEY segura, DEBUG=False, ALLOWED_HOSTS="tu-dominio.com"

# 5. Configurar unit de systemd y Nginx
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn

sudo cp deploy/nginx.conf /etc/nginx/sites-available/mvp-project
# Editar server_name con el dominio real
sudo ln -sf /etc/nginx/sites-available/mvp-project /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# 6. Emitir certificado SSL con Certbot (HTTPS forzado)
sudo certbot --nginx -d tu-dominio.com --non-interactive --agree-tos -m tu-email@dominio.com --redirect
```
**Resultado esperado**:
- `systemctl status gunicorn` en estado `active (running)`.
- `systemctl status nginx` en estado `active (running)`.
- Certificado SSL emitido y redirección HTTP -> HTTPS funcionando.

---

### Escenario 4: Validación del Despliegue Continuo (CD) Automático
Comprobar que una fusión a `main` actualiza el VPS de forma desatendida.

```bash
# Tras fusionar el PR a main en GitHub:
# Observar la ejecución del workflow '.github/workflows/cd.yml' en GitHub Actions.
```
**Resultado esperado**:
- GitHub Actions se conecta vía SSH al VPS.
- Ejecuta `deploy.sh`: sincroniza dependencias con `uv`, migra, recolecta estáticos y reinicia Gunicorn.
- El job finaliza con estado exitoso en menos de 60 segundos.

---

### Escenario 5: Cierre Definitivo de Fase 2 con `check_phase2.sh`
Ejecutar la validación final integral contra el entorno remoto en vivo.

```bash
# Desde la máquina de desarrollo:
HEALTH_URL=https://tu-dominio.com ./scripts/check_phase2.sh --remote JoelJohs/electrical-cpq-system
```

**Resultado esperado**:
```text
════════════════════════════════════════════════════════════════
Resultado: 16 PASS · 0 FAIL · 0 WARN · 0 PEND
Fase 2: EN OPERACIÓN ✅
════════════════════════════════════════════════════════════════
```
- Código de salida: `0`.
- Fase 2 formalmente completada y cerrada.
