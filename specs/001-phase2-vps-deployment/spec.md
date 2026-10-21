# Feature Specification: Cierre Operativo de Fase 2 y Despliegue en VPS Ubuntu 24.04 LTS

**Feature Branch**: `001-phase2-vps-deployment`

**Created**: 2026-10-18

**Status**: Ready for Planning

**Input**: User description: "Dentro tengo docs/basic-todo.md, en base eso, requiero que hagamos los specs para cerrar REALMENTE la fase 2: otra cosa, se subira a un vps con ubuntu lts 24.04 asi que todo lo de despliegue se debe enfocar a eso"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Despliegue y Verificación de Disponibilidad en VPS (Priority: P1)

Como operador o mantenedor del sistema, quiero desplegar la aplicación "Hello World" en un servidor VPS con Ubuntu 24.04 LTS y verificar su disponibilidad operativa mediante un endpoint de salud, para garantizar que el entorno de producción/staging es reproducible, seguro y responde confiablemente desde el primer día.

**Why this priority**: Es el núcleo pendiente para cerrar la Fase 2 de infraestructura. Sin un entorno remoto funcional en Ubuntu 24.04 LTS respondiendo al endpoint de salud, no existe ciclo de entrega real ni verificación contra el criterio de aceptación del proyecto.

**Independent Test**: Se puede probar de forma independiente configurando el VPS con el servicio web y consultando el endpoint `/health/` vía HTTP/HTTPS con `curl` y el script de verificación `scripts/check_phase2.sh`, recibiendo `{"status": "ok"}` con código HTTP 200.

**Acceptance Scenarios**:

1. **Given** un VPS configurado con Ubuntu 24.04 LTS con el servicio web activo y el socket de aplicación corriendo, **When** un cliente externo o el script de verificación realiza una petición `GET` a `/health/`, **Then** el servidor responde en menos de 2 segundos con código HTTP 200 y cuerpo JSON conteniendo `{"status": "ok"}`.
2. **Given** el entorno en el VPS, **When** se actualiza el código en el servidor y se reinicia el servicio de aplicación, **Then** el servicio se recupera automáticamente sin requerir intervención manual en dependencias del sistema operativo.

---

### User Story 2 - Integración Continua y Validación Automática de Calidad (Priority: P2)

Como desarrollador, quiero que cada Pull Request y cada cambio propuesto ejecute automáticamente el pipeline de Integración Continua (CI) en la nube, para asegurar que ningún código con fallos de formato, estilo, convenciones o pruebas rompa la rama principal (`main`).

**Why this priority**: La integridad de la base de código debe blindarse automáticamente antes de desplegar hacia el VPS, evitando que errores de configuración o regresiones lleguen al servidor remoto.

**Independent Test**: Se puede probar creando una rama de funcionalidad (`feat/...`), introduciendo un cambio (válido e inválido) y abriendo un Pull Request en el repositorio remoto, observando que GitHub Actions valide o rechace el cambio según los controles de calidad.

**Acceptance Scenarios**:

1. **Given** un Pull Request hacia la rama `main` con código que cumple formato (Ruff), linters y revisiones del framework, **When** el pipeline de CI finaliza su ejecución, **Then** el estado del check se reporta como exitoso (verde) y habilita la integración.
2. **Given** un Pull Request que viola las reglas de formateo o comprobaciones del sistema, **When** corre el pipeline de CI, **Then** el check falla inmediatamente, bloqueando la fusión errónea.

---

### User Story 3 - Protección de Rama Principal y Flujo de Entrega (Priority: P3)

Como administrador del proyecto, quiero establecer reglas de protección sobre la rama principal `main`, de modo que todo cambio ingrese exclusivamente mediante ramas de funcionalidad y validaciones comprobadas, eliminando modificaciones directas descontroladas.

**Why this priority**: Cierra el requerimiento pendiente de gobernanza de código de la Fase 2, formalizando la política de ramas y protegiendo el historial del repositorio.

**Independent Test**: Intentar hacer un push directo a `main` desde un entorno local sin pasar por PR o sin checks aprobados, verificando que la plataforma remota rechace la acción.

**Acceptance Scenarios**:

1. **Given** la rama `main` configurada con reglas de protección en el repositorio remoto, **When** un usuario intenta hacer un `git push origin main` directo, **Then** el repositorio remoto rechaza el push indicando que se requiere un Pull Request.
2. **Given** un Pull Request abierto hacia `main`, **When** las validaciones requeridas de CI no han completado exitosamente, **Then** la acción de fusión (merge) se mantiene bloqueada.

---

### Edge Cases

- ¿Qué sucede si el VPS experimenta un reinicio del sistema operativo? El servicio de la aplicación y el servidor web reverso deben iniciarse automáticamente mediante el gestor de servicios del sistema (systemd) sin intervención humana.
- ¿Qué ocurre si falla un paso intermedio durante el despliegue en el VPS (por ejemplo, fallo de sincronización de paquetes o migración)? El script o flujo de despliegue debe abortar de inmediato (`set -e`) y preservar la versión previa en ejecución para evitar tiempo de inactividad prolongado.
- ¿Cómo responde el endpoint de salud si el servidor de aplicaciones subyacente está caído pero el servidor web frontal está activo? El servidor web frontal debe devolver un error 502/504 identificable y el script de verificación `scripts/check_phase2.sh` debe clasificarlo inequívocamente como fallo (FAIL).
- ¿Qué sucede si se ejecutan múltiples despliegues concurrentes? Debe existir un bloqueo o serialización para evitar condiciones de carrera en el directorio de la aplicación en el VPS.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema de despliegue DEBE operar sobre un entorno de servidor VPS con sistema operativo Ubuntu 24.04 LTS.
- **FR-002**: El servidor VPS DEBE contar con un servidor web reverso configurado para exponer la aplicación en puertos estándar y gestionar archivos estáticos.
- **FR-003**: El demonio de la aplicación DEBE ejecutarse bajo supervisión de `systemd`, con reinicio automático ante fallos del proceso (`Restart=always`).
- **FR-004**: El despliegue continuo (CD) en el VPS DEBE gestionarse de forma automatizada mediante un pipeline de GitHub Actions vía conexión SSH segura tras cada fusión exitosa en la rama `main`.
- **FR-005**: El acceso y exposición pública del servicio en el VPS DEBE implementarse mediante un dominio propio configurado en el servidor web reverso, asegurado obligatoriamente con certificado SSL/TLS (HTTPS) emitido automáticamente vía Let's Encrypt / Certbot.
- **FR-006**: La política de protección sobre la rama `main` en GitHub DEBE exigir la ejecución exitosa (en verde) de los checks de CI antes de autorizar la fusión de un Pull Request, permitiendo la fusión directa por el autor sin requerir aprobación externa de terceros en esta etapa.
- **FR-007**: El pipeline de integración continua (CI) DEBE ejecutarse ante cada evento de Pull Request hacia `main` y en pushes a `main`, validando estilo, formato y comprobaciones de integridad.
- **FR-008**: El endpoint `/health/` DEBE retornar un estado HTTP 200 con respuesta JSON `{"status": "ok"}` cuando todos los componentes esenciales del servicio se encuentren operativos.
- **FR-009**: La ejecución del script de validación `scripts/check_phase2.sh` en modo remoto (`HEALTH_URL=<URL_VPS> ./scripts/check_phase2.sh --remote JoelJohs/electrical-cpq-system`) DEBE finalizar con 0 fallos (FAIL) y 0 pendientes (PEND), confirmando el cierre total de la Fase 2.

### Key Entities *(include if feature involves data)*

- **Servidor VPS (Host)**: Representa la instancia remota con Ubuntu 24.04 LTS donde se aloja el entorno de ejecución, los demonios de sistema y las configuraciones de red.
- **Servicio de Aplicación (Application Service)**: Representa el proceso supervisado por systemd que ejecuta el código backend y responde a peticiones a través del socket Unix/puerto local.
- **Servidor Web Reverso (Reverse Proxy)**: Representa el componente de borde encargado de recibir el tráfico HTTP/HTTPS, servir archivos estáticos directamente y enrutar las peticiones dinámicas al socket de la aplicación.
- **Regla de Protección de Rama (Branch Protection Rule)**: Políticas remotas aplicadas sobre `main` que rigen la exigencia de checks de CI y restricciones de fusión.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El comando `./scripts/check_phase2.sh` ejecutado con la URL remota del VPS y el repositorio remoto finaliza con exactamente 0 FAIL y 0 PEND ("Fase 2: EN OPERACIÓN").
- **SC-002**: El endpoint público `/health/` en el VPS responde con código de estado HTTP 200 y JSON `{"status": "ok"}` en menos de 2.0 segundos de tiempo de respuesta promedio.
- **SC-003**: El 100% de los Pull Requests hacia la rama principal ejecutan el pipeline de CI en menos de 3 minutos, impidiendo la fusión si se detectan errores de formato o consistencia.
- **SC-004**: Cualquier intento de push no autorizado o con validaciones reprobadas a `main` es rechazado por el repositorio remoto en el 100% de los casos.
- **SC-005**: El procedimiento de despliegue en el VPS actualiza el código y reinicia el servicio de aplicación en menos de 60 segundos sin requerir reinicio del servidor físico/virtual.

## Assumptions

- El repositorio remoto oficial del proyecto es `JoelJohs/electrical-cpq-system` alojado en GitHub.
- El usuario dispone de acceso con privilegios administrativos (`sudo` o `root`) en la instancia VPS con Ubuntu 24.04 LTS.
- Se cuenta con un nombre de dominio propio cuyos registros DNS de tipo A apuntan a la dirección IP pública del VPS Ubuntu 24.04 LTS.
- Las credenciales y claves privadas SSH requeridas para el despliegue automatizado hacia el VPS se configurarán como secretos protegidos en el repositorio de GitHub.
- La aplicación backend en esta fase corresponde a la estructura base y endpoint de salud existente, sin requerir persistencia de base de datos relacional externa adicional a la configurada por el sistema.
- Las herramientas de gestión de paquetes y entornos virtuales en el servidor VPS se alinean con la arquitectura definida en el repositorio (`uv`).
- La variable de entorno `SECRET_KEY` y configuraciones sensibles del entorno de producción se gestionan mediante archivo `.env` aislado en el VPS, excluido estrictamente del control de versiones.
- Las opciones seleccionadas (CD automatizado con GitHub Actions vía SSH, HTTPS con dominio propio y regla de protección sin revisión obligatoria por terceros) rigen el cierre de la Fase 2; cualquier transición posterior a aprobación obligatoria de PRs o esquemas manuales se realizará de forma diferida según indicación explícita del usuario.
