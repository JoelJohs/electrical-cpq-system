# Feature Specification: Arquitectura Base y Catálogo en Grafo Dirigido (Fase 3)

**Feature Branch**: `002-catalog-graph-architecture`

**Created**: 2026-10-18

**Status**: Ready for Planning

**Input**: User description: "## Fase 3: Arquitectura Base y Datos que se encuentra en el mismo todo. Modelo relacional de compatibilidades eléctricas como grafo dirigido en SQL (Product y ProductCompatibility), eliminando is_bidirectional, preservando semántica de negocio y estructura modular en Django."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Modelado y Consulta del Grafo de Compatibilidades Eléctricas (Priority: P1) 🎯 MVP

Como usuario del cotizador eléctrico (CPQ) o cliente, quiero seleccionar un equipo contenedor principal (ej. Tablero NQ) y obtener de forma instantánea todos los componentes principales compatibles (ej. interruptores termomagnéticos) y sus accesorios específicos (ej. kits de zapatas, contactos auxiliares), de modo que la cotización respete estrictamente la jerarquía física de montaje y no sugiera piezas incompatibles o relaciones lógicamente invertidas.

**Why this priority**: Es el núcleo del valor de negocio de la aplicación. Sin un grafo de compatibilidad dirigido y tipado, el sistema no puede guiar al usuario en la selección técnica correcta de productos eléctricos, arriesgando cotizaciones inviables o errores de ingeniería.

**Independent Test**: Consultar las compatibilidades de un producto principal y verificar que devuelva exclusivamente sus componentes y accesorios en la dirección correcta (`source` -> `target`), comprobando además que se rechacen auto-relaciones y relaciones duplicadas.

**Acceptance Scenarios**:

1. **Given** un producto de tipo contenedor/tablero (`TAB-NQ-225`) y un interruptor (`INT-QO-120`) vinculados mediante relación dirigida `COMPATIBLE_WITH`, **When** el usuario o sistema consulta los componentes compatibles del tablero, **Then** el sistema retorna el interruptor `INT-QO-120`.
2. **Given** un interruptor (`INT-QO-120`) y un contacto auxiliar (`ACC-AUX-QO`) vinculados mediante relación dirigida `COMPLEMENT_OF`, **When** se consultan los accesorios del interruptor, **Then** el sistema devuelve el contacto auxiliar, pero si se consultan los accesorios del contacto auxiliar hacia atrás, no se devuelve el interruptor como accesorio.
3. **Given** un producto cualquiera, **When** un operador o proceso intenta crear una relación de compatibilidad donde el origen y el destino sean el mismo producto (`source == target`), **Then** el sistema rechaza la operación con un error de validación de integridad.
4. **Given** una relación existente entre un producto origen, un producto destino y un tipo de relación, **When** se intenta insertar un duplicado idéntico, **Then** el sistema lo impide mediante restricción de unicidad compuesta.

---

### User Story 2 - Arquitectura Modular y Optimización de Consultas sin N+1 (Priority: P2)

Como desarrollador o servicio de cotización, quiero que la lógica de negocio esté organizada en una estructura modular desacoplada (separando entidades de dominio, servicios de consulta del grafo y controladores/vistas de presentación) y que las consultas de árboles de productos completos se ejecuten de manera eficiente sin sobrecargar la base de datos, para garantizar tiempos de respuesta inferiores a 50 milisegundos incluso con catálogos extensos.

**Why this priority**: Evita la degradación del rendimiento (`N+1 queries`) al renderizar tableros con múltiples circuitos y accesorios, facilitando el mantenimiento y la extensibilidad del sistema a medida que se agreguen módulos de reglas comerciales y cotización.

**Independent Test**: Ejecutar la consulta del árbol jerárquico completo para un tablero con múltiples componentes y accesorios, midiendo que el número de consultas SQL permanezca acotado y constante mediante precarga eficiente (`prefetch_related`).

**Acceptance Scenarios**:

1. **Given** un tablero con 10 interruptores asociados y cada uno con 2 accesorios, **When** se solicita la estructura completa de compatibilidades para cotizar, **Then** el servicio resuelve toda la jerarquía en un número fijo y mínimo de consultas SQL (máximo 2 consultas).
2. **Given** un cliente web o servicio externo que consulta la API de catálogo con orígenes permitidos, **When** se envía una petición con cabeceras CORS, **Then** el sistema responde con las cabeceras de autorización de origen y las políticas de seguridad configuradas.

---

### User Story 3 - Autenticación y Control de Acceso al Catálogo (Priority: P3)

Como administrador del sistema, quiero que la gestión de productos y reglas de compatibilidad requiera autenticación y permisos verificados, asegurando que las modificaciones técnicas sobre el catálogo solo puedan ser efectuadas por personal autorizado.

**Why this priority**: Protege la integridad de las reglas técnicas y los precios de los productos eléctricos contra modificaciones anónimas o accesos indebidos.

**Independent Test**: Intentar crear, modificar o eliminar productos y aristas de compatibilidad sin credenciales válidas y verificar el rechazo de la solicitud, y posteriormente autenticarse para confirmar que la operación se autorice.

**Acceptance Scenarios**:

1. **Given** un usuario no autenticado, **When** intenta acceder a las operaciones de creación o edición de productos, **Then** el sistema deniega el acceso con código de estado de autorización correspondiente.
2. **Given** un usuario autenticado con rol administrativo, **When** ingresa credenciales válidas y registra un producto nuevo, **Then** la operación se registra con trazabilidad de fechas de creación y actualización.

---

### Edge Cases

- ¿Qué sucede con relaciones simétricas o bidireccionales reales como `ALTERNATIVE_TO` (reemplazo o sustituto directo)? No se modelan con un booleano en el registro; se resuelven mediante consultas disyuntivas (`Q(source=p) | Q(target=p)`) preservando la pureza del grafo dirigido para las demás relaciones.
- ¿Cómo se maneja un producto inactivo (`is_active = False`) que aún posee aristas de compatibilidad en la base de datos? Las consultas de compatibilidad para cotización DEBEN filtrar automáticamente los productos inactivos para no ofrecer componentes descontinuados o agotados.
- ¿Qué ocurre si un producto contenedor tiene especificaciones técnicas en `specs` (JSONB) que no coinciden con los requerimientos de un componente (ej. voltaje o polos incompatibles)? El modelo debe registrar la arista formal y notas técnicas, permitiendo que la capa de validación de reglas de negocio valide atributos JSON de forma desacoplada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE modelar los productos del catálogo mediante una entidad `Product` que almacene identificador único (`sku`), nombre (`name`), identificador amigable (`slug`), tipo de producto (`product_type`), descripción, atributos técnicos flexibles (`specs` en formato estructurado JSON), estado de activación (`is_active`) y marcas temporales de auditoría (`created_at`, `updated_at`).
- **FR-002**: El tipo de producto (`product_type`) DEBE categorizarse al menos en: Tablero/Gabinete (`BOARD`), Componente Principal (`COMPONENT`) y Accesorio/Complemento (`ACCESSORY`).
- **FR-003**: El sistema DEBE modelar las compatibilidades mediante una tabla relacional de aristas dirigidas `ProductCompatibility` con referencia a producto origen (`source`), producto destino (`target`), tipo de relación (`relationship_type`), puntuación de prioridad (`score`) y notas técnicas descriptivas (`notes`).
- **FR-004**: Los tipos de relación (`relationship_type`) DEBEN incluir semántica de negocio diferenciada:
  - `COMPATIBLE_WITH`: El componente destino se instala o monta dentro del producto origen (ej. Tablero aloja Interruptor).
  - `COMPLEMENT_OF`: El producto destino es un accesorio o complemento funcional del origen (ej. Bobina o Zapata para Interruptor/Tablero).
  - `REQUIRES`: El producto origen exige obligatoriamente la inclusión del producto destino para operar.
  - `ALTERNATIVE_TO`: El producto destino es un reemplazo directo o equivalente funcional.
- **FR-005**: La relación de compatibilidad DEBE ser estrictamente dirigida: el producto `source` representa siempre el elemento base/anfitrión y `target` representa el elemento compatible o accesorio a agregar. Queda PROHIBIDO el uso de campos booleanos de bidireccionalidad (`is_bidirectional`) en el modelo de datos.
- **FR-006**: La base de datos DEBE impedir que un producto se relacione consigo mismo mediante una restricción de comprobación (`CheckConstraint`), complementada con validación en la capa de modelo.
- **FR-007**: La base de datos DEBE garantizar la unicidad de aristas dirigidas mediante restricción compuesta sobre `(source, target, relationship_type)`.
- **FR-008**: El modelo DEBE contar con índices compuestos sobre `(source, relationship_type)` y `(target, relationship_type)` para garantizar consultas de compatibilidad en cascada en tiempos inferiores a 10 milisegundos.
- **FR-009**: El sistema DEBE organizar el código en una estructura modular separando:
  - Capa de Dominio (Modelos de datos y validaciones de integridad).
  - Capa de Servicios y Selectores (Consultas especializadas de grafo sin N+1 queries).
  - Capa de Presentación / API (Vistas o controladores de catálogo y compatibilidad).
- **FR-010**: El sistema DEBE implementar autenticación para las operaciones administrativas de gestión de catálogo mediante el sistema nativo de autenticación de Django (Django Sessions, permisos de usuarios y Django Admin), permitiendo acceso seguro y autosuficiente sin dependencias de servicios externos.
- **FR-011**: La exposición de las consultas de catálogo para el cotizador DEBE implementarse mediante un framework formal de API dedicado (Django Ninja / Django REST Framework) con validación de esquemas tipados, serialización estructurada y documentación OpenAPI interactiva (`/docs` o `/swagger`).
- **FR-012**: Las conexiones de base de datos y políticas de persistencia DEBEN operar sobre un motor PostgreSQL contenerizado mediante Docker (`docker compose`) para el entorno local de desarrollo descartable y manipulable, desacoplado mediante la variable `DATABASE_URL` para permitir transición fluida hacia Docker o PostgreSQL gestionado en el VPS de producción.

### Key Entities *(include if feature involves data)*

- **Producto (`Product`)**: Nodo del catálogo eléctrico. Representa una pieza comercializable o configurable con sus especificaciones técnicas de placa y atributos físicos.
- **Compatibilidad de Producto (`ProductCompatibility`)**: Arista dirigida del grafo de catálogo. Define la relación de dependencia, alojamiento, complemento o sustitución técnica entre dos productos específicos.
- **Tipo de Producto (`ProductType`)**: Clasificación estructural del nodo (`BOARD`, `COMPONENT`, `ACCESSORY`).
- **Tipo de Relación (`RelationshipType`)**: Clasificación semántica de la arista (`COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Las consultas de componentes compatibles directos y accesorios de un producto se ejecutan en menos de 10 milisegundos bajo condiciones normales de carga.
- **SC-002**: La recuperación del árbol jerárquico completo (Tablero + Componentes + Accesorios de componentes) se resuelve en un máximo de 2 consultas SQL utilizando precarga de relaciones, eliminando por completo el problema de consultas N+1.
- **SC-003**: El 100% de los intentos de insertar una compatibilidad idéntica duplicada o una auto-relación (`source == target`) son rechazados a nivel de base de datos y de ORM.
- **SC-004**: El 100% de las operaciones de consulta de compatibilidades para cotización filtran automáticamente productos marcados como inactivos.
- **SC-005**: La suite de pruebas automatizadas de catálogo y compatibilidad cubre al menos el 90% de los flujos de consulta de grafo y validaciones de restricciones.

## Assumptions

- Los atributos técnicos de cada producto varían según su familia (polos, amperaje de disparo, voltaje, tipo de montaje), por lo que se utiliza un campo estructurado JSON (`specs`) validable a nivel aplicativo.
- La dirección de la relación es suficiente para modelar la jerarquía de un cotizador eléctrico sin requerir motores especializados de bases de datos de grafos (como Neo4j).
- Las políticas de seguridad básicas (CORS, cabeceras seguras) se basan en la configuración ya integrada en la Fase 2 del proyecto.
- El entorno de desarrollo local utilizará un contenedor Docker de PostgreSQL desechable y aislado mediante `docker compose`, permitiendo manipular y reiniciar datos de prueba sin comprometer el host, con la flexibilidad de usar Docker o PostgreSQL nativo en el VPS según convenga.
- La administración del catálogo se gestiona mediante Django Admin y autenticación de sesiones, mientras que las consultas de cotización se exponen como API REST tipada con documentación interactiva Swagger/OpenAPI.
