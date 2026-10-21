# Data Model & Operational Entities: Cierre Fase 2 (VPS Ubuntu 24.04 LTS)

**Feature**: `001-phase2-vps-deployment`  
**Date**: 2026-10-18  
**Status**: Ready  

Este documento define el modelo conceptual de las entidades de infraestructura, servicios del sistema operativo, procesos de despliegue y comprobaciones de salud involucradas en el cierre de la Fase 2.

---

## 1. Entidad: Servidor VPS Host (`VPSHost`)

Representa la instancia del servidor privado virtual donde se aloja la aplicación en producción o staging.

| Campo | Tipo | Descripción | Reglas de Validación |
|-------|------|-------------|----------------------|
| `ip_address` | String (IPv4) | Dirección IP pública accesible en internet | Formato IPv4 válido (ej. `198.51.100.24`) |
| `os_version` | String | Sistema operativo de la máquina | Obligatorio: `Ubuntu 24.04 LTS` |
| `deploy_user` | String | Usuario del sistema utilizado para despliegue | Existente en `/etc/passwd`, permisos `sudo` para `systemctl` |
| `app_directory` | String (Path) | Ruta base del repositorio clonado | Debe ser `/var/www/mvp-project` con permisos del usuario de despliegue y `www-data` |
| `uv_binary_path`| String (Path) | Ruta absoluta al ejecutable de `uv` | Debe ser `/usr/local/bin/uv` o `/root/.local/bin/uv` |

### Estados del Host
- `PROVISIONING`: En proceso de instalación de paquetes básicos (`git`, `nginx`, `certbot`, `uv`).
- `ACTIVE`: Totalmente aprovisionado y ejecutando los servicios.
- `MAINTENANCE`: Modo de mantenimiento o actualización del sistema base.
- `UNREACHABLE`: No responde a peticiones de red o SSH.

---

## 2. Entidad: Servicio de Aplicación (`GunicornService`)

Representa el demonio gestionado por `systemd` que ejecuta la aplicación Django a través del servidor WSGI Gunicorn.

| Campo | Tipo | Descripción | Reglas de Validación |
|-------|------|-------------|----------------------|
| `unit_file` | String (Path) | Archivo de unidad systemd | `/etc/systemd/system/gunicorn.service` |
| `socket_path` | String (Path) | Socket Unix para comunicación interproceso | `/run/gunicorn.sock` |
| `workers_count` | Integer | Número de procesos workers | Mínimo 2, por defecto 3 |
| `exec_command` | String | Comando de arranque supervisado | `/usr/local/bin/uv run gunicorn config.wsgi:application ...` |
| `user_group` | String | Usuario y grupo de ejecución del proceso | `www-data:www-data` |
| `restart_policy` | String | Política de reinicio ante fallos | `always` con `RestartSec=5` |

### Ciclo de Vida y Transiciones
```text
[Inactive] ---> (systemctl start) ---> [Active: Running]
     ^                                         |
     |---- (systemctl stop) -------------------|
     |                                         |
     |---- (crash / unhandled error) --------> [Failed] ---> (auto-restart) ---> [Active: Running]
                                               |
[Active: Running] ---> (systemctl restart) ----|
```

---

## 3. Entidad: Servidor Web Reverso (`NginxServer`)

Representa el servidor perimetral que recibe las conexiones entrantes en los puertos 80 y 443, sirve estáticos y delega el tráfico dinámico al socket WSGI.

| Campo | Tipo | Descripción | Reglas de Validación |
|-------|------|-------------|----------------------|
| `server_name` | String (FQDN) | Dominio o subdominio asignado | Debe coincidir con registros DNS A válidos |
| `listen_ports` | List[Integer] | Puertos abiertos de escucha | `80` (HTTP) y `443` (HTTPS) |
| `static_alias` | String (Path) | Directorio de archivos estáticos | `/var/www/mvp-project/staticfiles/` |
| `proxy_target` | String (URI) | Destino del proxy inverso | `http://unix:/run/gunicorn.sock` |
| `tls_certificate`| String (Path)| Certificado SSL emitido por Let's Encrypt | `/etc/letsencrypt/live/<domain>/fullchain.pem` |

### Estados
- `CONFIGURED`: Sintaxis de Nginx verificada (`nginx -t` exitoso).
- `ACTIVE`: Proceso Nginx en ejecución atendiendo tráfico.
- `SYNTAX_ERROR`: Archivo con directivas inválidas (bloquea recargas).

---

## 4. Entidad: Pipeline de Entrega Continua (`CDPipeline`)

Representa el flujo automatizado en GitHub Actions encargado de actualizar el VPS tras cada integración.

| Campo | Tipo | Descripción | Reglas de Validación |
|-------|------|-------------|----------------------|
| `workflow_file` | String (Path) | Definición YAML del workflow | `.github/workflows/cd.yml` |
| `trigger_event` | String | Evento que dispara el despliegue | `push` a la rama `main` |
| `target_host` | Secret | Host del VPS | GitHub Secret `VPS_HOST` |
| `ssh_user` | Secret | Usuario SSH | GitHub Secret `VPS_USER` |
| `ssh_key` | Secret | Clave privada SSH sin passphrase | GitHub Secret `SSH_PRIVATE_KEY` |
| `deploy_script` | String | Comando ejecutado en el VPS | `/var/www/mvp-project/deploy/deploy.sh` |

### Estados del Run
- `QUEUED`: En cola de GitHub Actions.
- `DEPLOYING`: Conexión SSH abierta y script `deploy.sh` en ejecución.
- `SUCCESS`: Los 5 pasos de `deploy.sh` completaron con código de salida 0.
- `FAILED`: Algún comando devolvió código de salida distinto de 0; notificación inmediata de error.

---

## 5. Entidad: Regla de Protección de Rama (`BranchProtectionRule`)

Representa las restricciones de gobernanza configuradas en GitHub para la rama `main`.

| Campo | Tipo | Descripción | Reglas de Validación |
|-------|------|-------------|----------------------|
| `branch` | String | Rama protegida | Obligatorio: `main` |
| `required_status_checks` | List[String] | Checks de CI obligatorios | Debe incluir `lint-and-test` |
| `require_pull_request` | Boolean | Exige PR para fusionar | `true` |
| `required_approving_review_count` | Integer | Número de aprobaciones humanas requeridas | `0` (en esta etapa inicial) |
| `enforce_admins` | Boolean | Aplica restricciones a administradores | `true` |

---

## 6. Entidad: Estado de Salud (`HealthStatus`)

Representa el resultado de la comprobación del endpoint de monitoreo `/health/`.

| Campo | Tipo | Descripción | Reglas de Validación |
|-------|------|-------------|----------------------|
| `status_code` | Integer | Código de estado HTTP retornado | Debe ser `200` |
| `response_body` | JSON | Cuerpo de la respuesta JSON | Debe contener `{"status": "ok"}` |
| `latency_ms` | Float | Tiempo transcurrido de la petición | Debe ser `< 2000 ms` |
| `timestamp` | ISO8601 | Momento de la consulta | Formato estándar de fecha/hora UTC |

### Estados de Salud
- `HEALTHY`: HTTP 200 + `{"status": "ok"}` + latencia en umbral.
- `DEGRADED`: Responde `{"status": "ok"}` pero la latencia supera 2.0 segundos.
- `UNHEALTHY`: Errores 502/504 (socket caído), 500 (error en Django) o timeout de conexión.
