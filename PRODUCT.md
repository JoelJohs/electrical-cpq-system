# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Django Templates + Tailwind CSS + Alpine.js / HTMX + Django Ninja + PostgreSQL

## Users

- **Clientes Externos, Contratistas y Proyectistas Eléctricos**: Usuarios que necesitan configurar tableros eléctricos, gabinetes y módulos derivados de forma autónoma (autoservicio), asegurando compatibilidad técnica y física antes de ordenar materiales o solicitar la integración.
- **Ejecutivos Comerciales y Personal Técnico de ABV Electric Supply**: Usuarios internos que reciben, consultan o asisten la configuración de listas de materiales para acelerar la atención a clientes.

## Product Purpose

Sistema web de configuración asistida de equipo eléctrico y armado de tableros (CPQ Técnico) basado en reglas de compatibilidad y grafos relacionales en SQL. Su objetivo es eliminar errores de incompatibilidad mecánica o eléctrica, automatizar la generación de la Lista de Materiales (*Bill of Materials* - BOM) con SKUs exactos y permitir a los clientes configurar ensambles viables en minutos.

## Positioning

Configurador técnico interactivo en tiempo real con validación rigurosa en el servidor (espacios, polos, amperajes, dependencias obligatorias `REQUIRES` y accesorios `COMPLEMENT_OF`), enfocado 100% en la precisión electro-mecánica (normas NOM-001-SEDE-2012, NEMA PB 1 e IEC 61439). A diferencia de cotizadores convencionales, opera como un despiece de ingeniería sin precios monetarios integrados en la base de datos.

## Operating Context

- Portal web de autoservicio accesible desde navegadores web en computadoras de escritorio, tablets y dispositivos móviles utilizados en oficinas técnicas, mostradores y obras.
- Interacción reactiva con representación esquemática de ranuras/polos del tablero y retroalimentación inmediata sobre piezas compatibles.

## Capabilities and Constraints

- **Capacidades Confirmadas**:
  - Selección de tablero o gabinete anfitrión.
  - Selección asistida de interruptores termomagnéticos y módulos derivados.
  - Validación física en tiempo real de espacios disponibles vs. ocupados.
  - Validación de límites de corriente nominal de barras principales.
  - Resolución obligatoria de dependencias (`REQUIRES`) con detección de ciclos.
  - Sugerencia automática de accesorios complementarios (`COMPLEMENT_OF`).
  - Generación y exportación de la Lista de Materiales (BOM) con SKUs, descripciones y cantidades.
- **Restricciones Durables (No Negociables)**:
  - **Cero precios en base de datos**: No se almacenan importes monetarios, divisas, subtotales ni impuestos (IVA).
  - **Autoridad final en el servidor**: Aunque la interfaz ofrezca retroalimentación visual reactiva con Alpine.js/HTMX, el backend Django valida y sella la conformidad del ensamble.
  - **Sin e-commerce transaccional**: No procesa pagos en línea con tarjeta ni timbrado fiscal SAT.

## Brand Commitments

- **Marca**: ABV ELECTRIC SUPPLY (Morelia, Michoacán).
- **Identidad Corporativa**: Alineación con el sitio web oficial documentado en `ABV-template.html` y activos en `ABV-template_files/`.
- **Logotipo Oficial**: Logotipo SVG institucional (`abv sin fondo.svg`).
- **Paleta y Tono**: Tono profesional, técnico, industrial y confiable. Colores azul corporativo, acentos ámbar/amarillo y fondos neutros de alto contraste.

## Evidence on Hand

- Plantilla y estilos corporativos: `ABV-template.html` y carpeta `ABV-template_files/` en la raíz del proyecto.
- Catálogo semilla y grafo funcional en `src/catalog/` (`TAB-NQ-225`, `INT-QO-120`, `INT-EDB-3100`, `ACC-AUX-QO`, `KIT-ZAP-225`).
- Especificación y contratos de la Fase 4 en `specs/004-core-cpq-happy-path/`.

## Product Principles

1. **Cero Precios en Base de Datos**: La herramienta resuelve la ingeniería y el despiece de materiales (BOM); no compite ni se mezcla con la contabilidad ni la lista de precios interna.
2. **Autoridad Absoluta en el Backend**: Toda regla física (polos, ranuras, corriente, compatibilidad) se verifica en el motor de reglas en el servidor.
3. **Autoservicio Guiado y Claro**: Clientes y contratistas configuran tableros sin requerir consulta exhaustiva de hojas de datos de fabricante.
4. **Fidelidad y Rigor Técnico**: Cada pieza sugerida o agregada respeta estrictamente los marcos, voltajes y especificaciones normativas.
5. **Identidad Visual Coherente**: La interfaz extiende de manera orgánica y natural la identidad de ABV Electric Supply.

## Accessibility & Inclusion

- Cumplimiento de pautas WCAG 2.1 nivel AA:
  - Contraste suficiente para visualización en pantallas bajo diversas condiciones de iluminación.
  - Señalización de errores de incompatibilidad con texto descriptivo claro y no únicamente mediante color.
  - Navegación accesible por teclado en la selección de piezas y configuración de ranuras.
