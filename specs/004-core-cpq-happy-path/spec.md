# Feature Specification: Flujo Principal de Configuración, Validación Eléctrica y Cotizaciones Técnicas (Fase 4 - Happy Path)

**Feature Branch**: `004-core-cpq-happy-path`

**Created**: 2026-10-21

**Status**: Ready for Planning

**Input**: User description: "# Fase 4: Desarrollo del Core (Happy Path). Implementar un flujo funcional de configuración y cotización que permita seleccionar productos, comprobar su compatibilidad, validar las restricciones de un tablero eléctrico y obtener una cotización o lista de materiales coherente con las reglas técnicas definidas..."

---

## Executive Summary & Context

La **Fase 4** representa la transición de la infraestructura de catálogo y grafo de compatibilidades (Fase 3) hacia la solución del problema nuclear de negocio de **ABV ELECTRIC SUPPLY**: automatizar la especificación técnica de materiales, la validación asistida de compatibilidad y el armado de tableros eléctricos.

Por decisión de negocio explícita, **el sistema no almacena ni procesa precios monetarios, divisas ni impuestos en la base de datos**. El sistema actúa como un **CPQ Técnico (Configurador Técnico y Generador de Listas de Materiales - BOM)** centrado en la viabilidad física, capacidad de polos/espacios, límites de corriente y despiece exacto de componentes y accesorios.

El principio rector de esta fase es que **la autoridad de las reglas técnicas y de negocio reside en el backend**. Las dos interfaces de usuario (vista comercial rápida y configurador técnico de tableros) se desarrollarán con **Django Templates + Tailwind CSS + Alpine.js / HTMX**, consumiendo los mismos contratos tipados de validación en Django Ninja.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Elaboración de Cotizaciones Técnicas y Selección Asistida (Priority: P1) 🎯 MVP Comercial

Como **Ejecutivo Comercial / Vendedor**,  
quiero crear una cotización técnica para un cliente o proyecto, agregar productos y componentes del catálogo con sus cantidades y recibir sugerencias inmediatas de refacciones y accesorios compatibles,  
para emitir especificaciones comerciales completas y técnicamente viables en minutos sin depender del área de ingeniería.

**Why this priority**: Resuelve la necesidad inmediata de digitalizar la captura de listas de materiales de venta y orientar al vendedor en la venta cruzada (*cross-selling*) de accesorios complementarios.

**Independent Test**: Un usuario crea una cotización técnica asignando cliente/proyecto, añade interruptores principales, el sistema le sugiere accesorios compatibles (contactos auxiliares, kits de montaje) y le permite guardar la configuración en estado borrador con cantidades y códigos exactos.

**Acceptance Scenarios**:

1. **Given** un vendedor autenticado, **When** crea una nueva cotización asignando nombre de cliente o referencia de proyecto, **Then** el sistema genera una cotización en estado inicial `DRAFT` con folio secuencial único (ej. `COT-2026-0001`) y marca de tiempo.
2. **Given** una cotización en borrador, **When** el vendedor añade un producto con su cantidad, **Then** el sistema registra la partida (`QuoteItem`), valida que el producto esté activo y actualiza el conteo de ítems de la cotización.
3. **Given** un producto agregado a la cotización, **When** el vendedor consulta sus complementos, **Then** el sistema muestra los accesorios vinculados por aristas `COMPLEMENT_OF` para agregarlos con un solo clic.

---

### User Story 2 - Motor de Validación de Restricciones Técnicas y Despiece BOM (Priority: P2) 🎯 Core Técnico

Como **Ingeniero Integrador de Tableros Eléctricos**,  
quiero que el sistema verifique en tiempo real las restricciones físicas de un tablero (espacios/polos disponibles, capacidad máxima de corriente y dependencias obligatorias de accesorios `REQUIRES`),  
para saber con certeza técnica si un ensamble es viable y obtener la lista de despiece de materiales (*Bill of Materials* - BOM) lista para taller sin errores de montaje físico.

**Why this priority**: Elimina los reprocesos en taller de armado causados por componentes que no caben físicamente en el gabinete, interruptores de marco incompatible o accesorios obligatorios omitidos.

**Independent Test**: Un integrador selecciona un tablero NQ de 30 polos y añade interruptores derivados. Al superar los 30 espacios o intentar omitir un accesorio con relación `REQUIRES`, el sistema rechaza la configuración con un informe estructurado de errores (`valid: false`, `errors: [...]`); al corregir las partidas, emite el BOM estructurado.

**Acceptance Scenarios**:

1. **Given** un tablero con capacidad de 30 polos y 24 polos ya ocupados, **When** el usuario intenta agregar un interruptor de 3 polos (3 espacios), **Then** el sistema valida la ocupación física, descuenta los espacios y reporta 3 espacios restantes.
2. **Given** un tablero al que se intenta agregar un componente que excede la capacidad remanente de espacios o el límite de amperaje de barras, **When** se solicita la validación, **Then** el sistema devuelve un estado inválido (`valid: false`) con el código específico `INSUFFICIENT_SPACE` o `AMPERAGE_EXCEEDED` indicando espacios requeridos vs. disponibles.
3. **Given** un componente principal que tiene configurada una relación obligatoria `REQUIRES` hacia un accesorio (ej. arrancador que exige relé de sobrecarga), **When** se evalúa la cotización sin dicho accesorio, **Then** el sistema señala el error `MISSING_REQUIRED_ACCESSORY` indicando el producto mandatorio faltante.
4. **Given** un ensamble de tablero completamente conforme con las reglas técnicas, **When** el integrador solicita el despiece, **Then** el sistema genera la Lista de Materiales (BOM) estructurada en < 2 segundos.

---

### User Story 3 - API Tipada del Configurador y Transiciones de Estado (Priority: P3)

Como **Desarrollador / Sistema Consumidor**,  
quiero interactuar con endpoints REST documentados que permitan gestionar cotizaciones técnicas, validar configuraciones en memoria y transicionar estados (`DRAFT` → `VALIDATED` → `SENT` → `ACCEPTED`),  
para que cualquier interfaz o cliente pueda ejecutar el ciclo de vida completo de la cotización con garantías de integridad transaccional.

**Why this priority**: Desacopla la lógica de negocio y las validaciones de las capas visuales, permitiendo probar exhaustivamente el Happy Path mediante contratos de API y Swagger.

**Independent Test**: Ejecutar vía HTTP (`POST /api/quotes`, `POST /api/quotes/{id}/items`, `POST /api/quotes/{id}/validate`, `GET /api/quotes/{id}/bom`) la creación, modificación, validación y despiece de una cotización, confirmando códigos HTTP 200/201/400/404 y esquemas JSON estrictos.

**Acceptance Scenarios**:

1. **Given** un cliente HTTP enviando una solicitud a `/api/quotes/{id}/validate`, **When** la configuración contiene violaciones técnicas, **Then** la API responde código 200 con `{ "valid": false, "errors": [...] }` detallando cada regla rota con códigos numéricos y explicaciones.
2. **Given** una cotización que ha pasado exitosamente la validación técnica, **When** el usuario ejecuta la transición a estado `VALIDATED`, **Then** el sistema actualiza su estado y permite marcarla como `SENT`.
3. **Given** una cotización en estado `SENT` o `ACCEPTED`, **When** se intenta modificar o eliminar una partida, **Then** el sistema rechaza la mutación con un error de operación no permitida en estado de solo lectura.

---

### User Story 4 - Interfaces Web Asistidas con Django Templates + Tailwind + Alpine.js (Priority: P4)

Como **Usuario Final (Vendedor o Integrador)**,  
quiero operar en una interfaz web reactiva y clara que muestre las alertas de compatibilidad, indicadores visuales de ocupación de espacios y botones directos de acción,  
para completar mi flujo de trabajo diario de forma fluida sin lidiar con catálogos manuales ni cálculos en hojas de cálculo.

**Why this priority**: Materializa el valor de negocio para los operadores finales en mostrador de ventas y en mesa de ingeniería dentro de una arquitectura monolítica ágil y sin dependencias externas complejas.

**Independent Test**: Un vendedor elabora una cotización comercial fluida en la vista rápida agregando accesorios recomendados; un integrador configura un tablero en el configurador técnico visualizando la barra de ocupación de polos en tiempo real.

**Acceptance Scenarios**:

1. **Given** un vendedor buscando un interruptor en la vista comercial, **When** lo selecciona, **Then** el panel lateral despliega de inmediato los complementos y accesorios sugeridos con casillas para añadirlos en un clic.
2. **Given** un integrador en el configurador de tableros, **When** agrega o retira interruptores derivados, **Then** el indicador de espacios ocupados se actualiza dinámicamente y resalta en rojo si se sobrepasa el límite.
3. **Given** una cotización con errores técnicos, **When** el usuario intenta confirmarla, **Then** la interfaz resalta las partidas en conflicto con explicaciones amigables y sugiere la acción correctiva.

---

### Edge Cases

- **Sobrecupo físico exacto**: Intentar añadir un interruptor de 2 polos cuando queda exactamente 1 espacio físico libre en el tablero debe ser bloqueado con el error `INSUFFICIENT_SPACE`.
- **Accesorios con marco incompatible**: Intentar vincular un contacto auxiliar diseñado para marco QO en un interruptor de marco EDB debe ser rechazado por incompatibilidad mecánica.
- **Ciclos o dependencias circulares en `REQUIRES`**: Si el producto A requiere B, y el producto B requiere A, el motor de validación debe detectar la satisfacción mutua de ambas condiciones sin entrar en recursión infinita.
- **Intentos de mutación en cotizaciones aceptadas**: Cualquier intento de modificar partidas en una cotización en estado `SENT`, `ACCEPTED` o `CANCELLED` debe ser denegado.
- **Cotizaciones sin partidas**: Una cotización sin ningún producto no puede transicionar a estado `VALIDATED` ni generar un BOM.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE modelar las entidades `Quote` y `QuoteItem` con campos normalizados para folio único, cliente/proyecto, estado, notas técnicas y fechas.
- **FR-002**: El sistema DEBE gestionar un ciclo de vida con estados formales: `DRAFT` (Borrador), `VALIDATED` (Validado técnicamente), `SENT` (Emitido al cliente), `ACCEPTED` (Aprobado) y `CANCELLED` (Cancelado).
- **FR-003**: El sistema DEBE bloquear la edición o eliminación de partidas en cotizaciones que se encuentren en estados distintos a `DRAFT` y `VALIDATED`.
- **FR-004**: El sistema DEBE implementar un motor de validación técnica independiente de la interfaz gráfica que reciba una cotización o ensamble y evalúe:
  1. Compatibilidad de montaje físico entre gabinete/anfitrión y derivados.
  2. Capacidad máxima de espacios/polos disponibles vs. ocupados.
  3. Límite de corriente máxima admisible.
  4. Satisfacción de dependencias mandatorias (`REQUIRES`).
- **FR-005**: El motor de validación DEBE emitir respuestas estructuradas indicando el estado booleano de validez (`valid: true/false`) y un arreglo de errores con códigos tipados (`INSUFFICIENT_SPACE`, `AMPERAGE_EXCEEDED`, `MISSING_REQUIRED_ACCESSORY`, `INCOMPATIBLE_MOUNTING`) acompañados de explicaciones legibles y detalles cuantitativos.
- **FR-006**: El sistema DEBE permitir la validación de configuraciones "en caliente" (en memoria o sobre cotizaciones guardadas) sin forzar la persistencia de ensambles inválidos.
- **FR-007**: El sistema DEBE generar el despiece técnico o Lista de Materiales (*Bill of Materials* - BOM) agrupando componentes principales, accesorios de barra y complementos de montaje con sus códigos SKU y cantidades totales calculadas.
- **FR-008**: El sistema DEBE exponer endpoints REST documentados en Swagger mediante Django Ninja para la creación, consulta, modificación, validación y exportación de BOM de cotizaciones.
- **FR-009**: El sistema DEBE proveer una interfaz web comercial optimizada para ejecutivos de ventas con búsqueda reactiva de catálogo y sugerencias automáticas de accesorios complementarios (`COMPLEMENT_OF`).
- **FR-010**: El sistema DEBE proveer un configurador técnico de tableros para ingenieros integradores con representación visual paramétrica de espacios de ranura y alertas inmediatas de incompatibilidad.

### Non-Functional Requirements & Architecture

- **NFR-001 (Consistencia Transaccional)**: Todas las operaciones de modificación de cotizaciones y actualización de partidas deben ejecutarse bajo transacciones atómicas (`transaction.atomic`) en base de datos.
- **NFR-002 (Rendimiento del Motor de Reglas)**: La evaluación de reglas técnicas y cálculo de BOM debe completarse en menos de 2 segundos para ensambles de hasta 50 partidas.
- **NFR-003 (Separación Limpia de Capas)**: La lógica de negocio y las validaciones deben residir en la capa de servicios y dominio (`services.py`, `rules.py`), reutilizando los selectores de grafo existentes sin duplicar consultas SQL.
- **NFR-004 (Stack de UI)**: Las interfaces web deben implementarse mediante Django Templates enriquecidas con Tailwind CSS y Alpine.js / HTMX, manteniendo un monolito ágil y mantenible.

---

## Success Criteria *(mandatory)*

- **SC-001 (Prevención de Errores Técnicos)**: **0% de falsos negativos** en la detección de sobrecupo de espacios y en la omisión de accesorios obligatorios (`REQUIRES`).
- **SC-002 (Velocidad de Validación)**: El motor de validación emite el dictamen técnico y la estructura de BOM en **menos de 2 segundos** en el 95% de las invocaciones.
- **SC-003 (Completitud del Happy Path)**: Un usuario puede recorrer el flujo completo de principio a fin (Crear cotización técnica → Seleccionar tablero → Agregar interruptores compatibles → Resolver dependencias → Validar ensamble → Generar Lista de Materiales BOM) de manera autónoma y sin interrupciones.
- **SC-004 (Operatividad en Producción)**: 100% de cobertura en pruebas automatizadas sobre las reglas críticas de espacios, corrientes y dependencias obligatorias.

---

## Key Entities & Data Model Relationships

```text
  [ Product ] (Catálogo existente - Fase 3)
      │
      ├───[ ProductCompatibility ] (Grafo de compatibilidad existente - Fase 3)
      │
      └───[ QuoteItem ] (Partida de cotización / ensamble)
              • quantity: PositiveIntegerField
              • notes: CharField
              • slot_position: PositiveIntegerField (Opcional, para tableros)
              │ N
              ▼ 1
          [ Quote ] (Cotización Técnica / Configuración de Tablero)
              • folio: CharField (Único, ej. COT-2026-0001)
              • client_name: CharField
              • project_reference: CharField
              • status: TextChoices (DRAFT, VALIDATED, SENT, ACCEPTED, CANCELLED)
              • is_board_assembly: BooleanField
              • board_product: ForeignKey(Product, optional, related_name="board_quotes")
              • notes: TextField
              • created_at: DateTimeField
              • updated_at: DateTimeField
```

---

## Out of Scope (Delimitaciones de la Fase 4)

- **Precios monetarios, divisas y cálculo de impuestos**: El sistema no gestiona precios, divisas ni IVA; su alcance es estrictamente la validación técnica, selección asistida y despiece BOM.
- **Pasarelas de pago y facturación electrónica**: Fuera de alcance (mantenido en el ERP contable de la empresa).
- **Validación formal de los 30 casos históricos**: La ejecución de la batería completa con el comité de ingeniería corresponde a la Fase 5.
- **Modelado tridimensional CAD/3D interactivo**: La interfaz de tableros se diseñará como un esquema paramétrico 2D claro y funcional.
- **Despliegue productivo en VPS con HTTPS**: Corresponde a la Fase 6.

---

## Resolved Business Decisions

| Pregunta | Decisión Tomada | Justificación e Impacto |
| :--- | :--- | :--- |
| **Q1: Precios en Catálogo y Cotizaciones** | **Sin precios monetarios en base de datos** | La herramienta se enfoca en resolver el problema nuclear de ingeniería: compatibilidad electro-mecánica, validación de tableros y generación del BOM. |
| **Q2: Impuestos y Moneda Comercial** | **Sin impuestos ni divisas** | Al no manejar importes monetarios, se eliminan cálculos fiscales y monedas, simplificando la precisión técnica de las partidas. |
| **Q3: Stack de Frontend** | **Django Templates + Tailwind CSS + Alpine.js / HTMX** | Permite construir interfaces reactivas e interactivas dentro del mismo entorno Django sin la sobrecarga de un pipeline SPA desacoplado. |
