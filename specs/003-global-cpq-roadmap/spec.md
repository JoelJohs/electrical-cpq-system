# Feature Specification: Sistema Web de Selección y Cotización Eléctrica (CPQ) y Armado de Tableros

**Feature Branch**: `003-global-cpq-roadmap`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Muestrame el Roadmap y de ser posible detallarlo un poco mas. En pocas palabras, unicamente hacer el spec global del proyecto, y modificar unicamente el roadmap con ello. En el root de este proyecto coloque el bosquejo, puedes leerlo para saber de que va el proyecto, una vez lo leas y tengas la información lo puedes borrar"

---

## Executive Summary & Context

En **ABV ELECTRIC SUPPLY**, la comercialización, especificación y ensamblaje de equipo eléctrico industrial actualmente se realiza de forma manual y empírica, utilizando catálogos impresos y hojas de cálculo dispersas. Esta situación ocasiona errores de incompatibilidad en cotizaciones (selección de accesorios de marcas/marcos incorrectos u omisión de piezas mandatorias), demoras críticas por dependencia constante del área de ingeniería, reprocesos en taller de ensamble por piezas que no acoplan físicamente, y pérdida de oportunidades de venta cruzada (*cross-selling*).

El objetivo global del proyecto es implementar un **Sistema Web de Selección Basado en Reglas de Negocio (CPQ - Configure, Price, Quote)** que guíe la cotización comercial y el armado asistido de tableros eléctricos en tiempo real, garantizando 100% de consistencia técnica y automatizando la generación de listas de materiales (*Bill of Materials* - BOM).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cotización Rápida Comercial con Sugerencia Asistida (Priority: P1) 🎯 MVP Comercial

Como **Ejecutivo del Área Comercial y de Ventas**,  
quiero capturar una cotización seleccionando un producto base o gabinete y recibir recomendaciones automáticas e inmediatas de accesorios compatibles y refacciones mandatorias,  
para emitir propuestas comerciales completas y técnicamente viables en minutos sin tener que solicitar validación manual al equipo de ingeniería.

**Why this priority**: Es la necesidad comercial más urgente para eliminar el cuello de botella en ventas, acortar el ciclo de cotización y capturar oportunidades de venta cruzada (*cross-selling*).

**Independent Test**: Un vendedor selecciona un interruptor o producto base; el sistema le presenta inmediatamente los accesorios correspondientes (contactos auxiliares, bobinas) con compatibilidad validada y le impide omitir complementos mandatorios, permitiendo exportar un resumen preliminar de cotización.

**Acceptance Scenarios**:

1. **Given** un ejecutivo comercial elaborando una cotización, **When** selecciona un interruptor termomagnético específico, **Then** el sistema presenta únicamente los accesorios y complementos mecánicamente y eléctricamente compatibles (ej. contactos auxiliares, bobinas) ordenados por relevancia.
2. **Given** un producto base que exige un accesorio obligatorio para su puesta en marcha (ej. relé de sobrecarga en un arrancador), **When** el vendedor intenta agregar solo el producto base, **Then** el sistema alerta sobre la dependencia obligatoria e incorpora el accesorio requerido en la propuesta.
3. **Given** una cotización comercial finalizada, **When** el vendedor confirma la selección, **Then** el sistema genera el resumen valorizado de la cotización con los códigos exactos de producto en menos de 2 segundos.

---

### User Story 2 - Armado y Configuración Asistida de Tableros Eléctricos con BOM (Priority: P2)

Como **Ingeniero Integrador de Tableros Eléctricos**,  
quiero configurar un tablero eléctrico mediante un entorno asistido que valide en tiempo real la capacidad de espacios/polos, capacidades de corriente nominal y compatibilidad de montaje físico,  
para obtener la lista exhaustiva de materiales (*Bill of Materials* - BOM) lista para ensamble en taller sin riesgo de fallas mecánicas en el montaje.

**Why this priority**: Garantiza la estandarización técnica de ingeniería, previene reprocesos en taller de integración y automatiza el despiece técnico requerido para compras y producción.

**Independent Test**: Un integrador selecciona un gabinete/tablero base (ej. tipo NQ de 30 polos) y añade múltiples interruptores y kits de zapatas; el sistema valida la suma de polos, advierte cuando se alcanza el límite físico o de corriente y genera el BOM desglosado.

**Acceptance Scenarios**:

1. **Given** un tablero con capacidad de 30 espacios físicos, **When** el integrador añade interruptores derivados, **Then** el sistema descuenta los espacios disponibles en tiempo real e impide exceder la capacidad total del gabinete.
2. **Given** un interruptor de un tipo de montaje o familia incompatible con el chasis del tablero (ej. atornillable vs. enchufable sin el adaptador requerido), **When** el usuario intenta agregarlo al tablero, **Then** el sistema bloquea la acción o condiciona su inclusión al adaptador de montaje correspondiente.
3. **Given** un ensamble de tablero completamente validado, **When** el integrador solicita el despiece, **Then** el sistema emite el BOM estructurado conteniendo gabinete, derivados, accesorios de barra y complementos de montaje con 0% de errores de ensamble físico.

---

### User Story 3 - Gobernanza y Administración del Catálogo de Reglas Técnicas (Priority: P3)

Como **Administrador del Sistema / Ingeniero de Catálogo**,  
quiero gestionar el catálogo de productos, atributos técnicos (voltajes, polos, capacidades, dimensiones) y definir las aristas dirigidas de compatibilidad (`COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`),  
para que el motor de reglas mantenga actualizado el conocimiento técnico de las marcas y familias electro-industriales sin necesidad de reprogramar el sistema.

**Why this priority**: Proporciona sostenibilidad al motor de reglas a mediano y largo plazo conforme los fabricantes introducen nuevas líneas de producto y accesorios.

**Independent Test**: El administrador registra un nuevo accesorio y lo vincula como complemento de un interruptor existente desde la interfaz administrativa; de inmediato, dicho accesorio queda disponible para recomendación en el flujo comercial.

**Acceptance Scenarios**:

1. **Given** un administrador autenticado en la plataforma, **When** da de alta una nueva relación de compatibilidad técnica entre dos productos, **Then** el sistema valida que no exista auto-relación ni duplicidad de aristas antes de persistirla.
2. **Given** un producto que es descontinuado o reemplazado por el fabricante, **When** el administrador lo configura como inactivo o le asocia una relación de alternativa (`ALTERNATIVE_TO`), **Then** el sistema sugiere automáticamente el reemplazo vigente en las nuevas cotizaciones.

---

### Edge Cases

- **Saturación de capacidad física en tablero**: ¿Qué ocurre si un integrador intenta agregar un interruptor de 3 polos cuando al tablero solo le quedan 2 espacios disponibles? El sistema debe emitir una alerta explícita de sobrecupo y bloquear la inserción o sugerir un gabinete de mayor capacidad.
- **Accesorios con dependencias cruzadas**: ¿Qué ocurre si un accesorio seleccionado requiere a su vez un voltaje de control específico no suministrado en el ensamble? El sistema debe señalar la advertencia de incompatibilidad de control en el resumen de validación.
- **Discontinuidad de inventario o códigos descatalogados**: ¿Cómo maneja el sistema cotizaciones guardadas con productos que cambiaron de estado a inactivos? El sistema debe alertar al usuario y sugerir el producto equivalente definido en las aristas `ALTERNATIVE_TO`.
- **Acceso concurrente de cotizaciones**: ¿Cómo se gestionan múltiples solicitudes de cotización simultáneas? El motor de reglas debe ser sin estado (*stateless*), procesando validaciones independientes en menos de 2 segundos.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE mantener un catálogo centralizado de productos eléctricos clasificados por tipo (`BOARD`, `COMPONENT`, `ACCESSORY`) con atributos técnicos normalizados (amperaje, polos, voltaje, tipo de montaje).
- **FR-002**: El sistema DEBE modelar las relaciones de compatibilidad técnica mediante un grafo dirigido que preserve la asimetría física de los productos (`source` anfitrión hacia `target` componente/accesorio) y la semántica de relación (`COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`).
- **FR-003**: El sistema DEBE validar de forma obligatoria las dependencias requeridas (`REQUIRES`), impidiendo generar una cotización final si faltan componentes indispensables para la operación del equipo.
- **FR-004**: El sistema DEBE permitir a los ejecutivos comerciales buscar productos y visualizar recomendaciones automáticas de accesorios y complementos compatibles ordenados por prioridad de recomendación.
- **FR-005**: El sistema DEBE proporcionar a los ingenieros integradores un módulo de configuración de tableros que contabilice en tiempo real los espacios ocupados/disponibles y valide límites máximos de corriente y montaje.
- **FR-006**: El sistema DEBE generar la lista desglosada de materiales (*Bill of Materials* - BOM) con códigos exactos, descripciones y cantidades requeridas para el ensamble en taller.
- **FR-007**: El sistema DEBE proteger la gestión y edición del catálogo y sus reglas mediante autenticación y permisos de usuario diferenciados (Vendedor, Integrador, Administrador).
- **FR-008**: El sistema DEBE responder a las consultas de compatibilidad y generación de árbol de cotización en un tiempo no mayor a 2 segundos.

### Non-Functional Requirements & Standards

- **NFR-001 (Precisión técnica)**: Las recomendaciones emitidas por el motor de reglas deben garantizar el 100% de coherencia con las hojas técnicas de fabricante y normativas de referencia (NOM-001-SEDE-2012, NEMA PB 1, IEC 61439-1/2).
- **NFR-002 (Rendimiento)**: El motor de consulta debe resolver árboles de compatibilidad en un número fijo y mínimo de consultas a la base de datos sin incurrir en cuellos de botella $N+1$.
- **NFR-003 (Disponibilidad y Despliegue)**: El sistema debe estar preparado para ejecutarse en entorno de pruebas (*staging*) en servidor VPS con Linux Ubuntu 24.04 LTS, Nginx, Gunicorn y base de datos relacional.

---

## Success Criteria *(mandatory)*

- **SC-001 (Tiempo de cotización)**: El tiempo promedio para elaborar una cotización completa de equipo eléctrico con accesorios se reduce en al menos un **80%** (de ~30 minutos manuales a menos de 5 minutos).
- **SC-002 (Efectividad técnica)**: **100% de efectividad** (0 errores de incompatibilidad física o eléctrica) en una batería formal de al menos **30 casos reales de prueba** de cotización e integración de tableros evaluados con el área de ingeniería.
- **SC-003 (Velocidad de respuesta)**: El 95% de las consultas de recomendación de piezas y resolución de árbol de componentes responden en **menos de 2 segundos**.
- **SC-004 (Autonomía comercial)**: Los ejecutivos de venta pueden completar cotizaciones de productos estándar y tableros sin requerir consulta o asistencia previa del departamento de ingeniería en al menos el **90%** de los casos rutinarios.
- **SC-005 (Adopción y Capacitación)**: El **100% del personal clave** del área comercial y de integradores de ABV Electric Supply recibe capacitación formal y cuenta con manuales de usuario y documentación operativa.

---

## Key Entities & Data Model Relationships

```text
  [ Product ] (Nodos)
      │ 1
      │
      ├───[ ProductCompatibility ] (Aristas Dirigidas: source -> target)
      │         • relationship_type: COMPATIBLE_WITH | COMPLEMENT_OF | REQUIRES | ALTERNATIVE_TO
      │         • score, notes
      │
      └───[ QuoteItem ] (Líneas de cotización)
                │ N
                ▼ 1
          [ Quote ] (Cotización / Configuración de Tablero)
                • status, client_reference, total_spaces, used_spaces
```

---

## Out of Scope (Delimitaciones Explícitas)

1. **Pasarelas de pago transaccionales en línea**: No se procesarán cobros con tarjeta de crédito/débito ni checkout e-commerce en esta etapa del proyecto.
2. **Facturación electrónica fiscal (CFDI / SAT)**: El sistema generará cotizaciones y listas de materiales (BOM); la emisión de facturas fiscales se mantiene en el ERP/sistema contable actual de la empresa.
3. **Renderizado o modelado CAD/3D interactivo**: La interfaz representará las posiciones y ocupación de espacios de forma esquemática y paramétrica bidimensional, sin visualización tridimensional en tiempo real.
