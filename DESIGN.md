---
name: "ABV Electric Supply - Technical CPQ & Board Configurator"
description: "Sistema de diseño técnico e industrial para el configurador de tableros y selección de equipo eléctrico"
colors:
  primary: "#1e1e1e"
  primary-hover: "#333333"
  accent: "#007bff"
  accent-hover: "#0056b3"
  success: "#28a745"
  success-hover: "#218838"
  warning: "#ffc107"
  danger: "#dc3545"
  neutral-bg: "#e6e8e5"
  surface: "#ffffff"
  surface-alt: "#f0f4f8"
  text-main: "#1e1e1e"
  text-muted: "#555555"
  border: "#c8d0d8"
  border-subtle: "#e0e0e0"
typography:
  display:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "clamp(1.75rem, 3.5vw, 2.25rem)"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  title:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "normal"
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.02em"
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace"
    fontSize: "0.85rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "normal"
rounded:
  sm: "4px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 18px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 18px"
  button-accent-hover:
    backgroundColor: "{colors.accent-hover}"
  button-success:
    backgroundColor: "{colors.success}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 18px"
  card-panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "20px"
---

# Design System: ABV Electric Supply CPQ

## 1. Overview

Este sistema de diseño formaliza el lenguaje visual de **ABV ELECTRIC SUPPLY** para el Configurador Técnico de Tableros Eléctricos y Sistema CPQ (Configure, Price, Quote - sin precios).

El producto opera en modo **Operate & Persuade**: proporciona una experiencia de autoservicio clara, técnica, estructurada y confiable tanto para clientes externos (ingenieros proyectistas, contratistas eléctricos) como para el equipo técnico y comercial interno.

### Principios Visuales Clave
1. **Rigor Técnico e Industrial**: La interfaz proyecta ingeniería sólida y precisión eléctrica. Emplea alto contraste, tipografía monoespaciada para códigos SKU y parámetros numéricos (amperaje, polos, voltaje), e indicadores de estado inequívocos.
2. **Cero Precios, Máxima Claridad de Ensamblaje**: El foco visual está puesto en la capacidad física del gabinete (ranuras/polos), la viabilidad de montaje y el despiece de materiales (*BOM*), sin elementos de checkout o cobro.
3. **Coherencia Corporativa Directa**: Adopta fielmente los colores institucionales (grafito/negro `#1E1E1E`, azul eléctrico `#007BFF`, acentos de seguridad verde `#28A745`, y fondo industrial gris claro `#E6E8E5`), extraídos del sitio web oficial de ABV Electric Supply.

---

## 2. Colors

La paleta cromática se deriva de la identidad institucional de ABV Electric Supply y la señalética electro-industrial estándar:

### 2.1 Colores Principales y Semánticos
- **Primary (`#1E1E1E`)**: Grafito profundo / carbón industrial. Utilizado en la barra de navegación superior, encabezados mayores, botones primarios de acción y bordes destacados.
- **Accent (`#007BFF`)**: Azul eléctrico industrial. Utilizado para elementos activos, foco de selección, enlaces clave y botones de configuración de componentes.
- **Success (`#28A745`)**: Verde de conformidad técnica / seguridad. Utilizado para el estado de ensamble válido, ranuras disponibles conformes y botón de generación de BOM.
- **Warning (`#FFC107`)**: Ámbar / amarillo de atención. Utilizado para advertencias de capacidad próxima al límite y recomendaciones de accesorios no obligatorios.
- **Danger (`#DC3545`)**: Rojo de alerta / incompatibilidad. Utilizado para sobrecupo de espacios físicos, exceso de amperaje o accesorios obligatorios omitidos (`REQUIRES`).

### 2.2 Superficies y Fondos
- **Page Background (`#E6E8E5`)**: Gris neutro industrial con matiz cálido que reduce el cansancio visual frente a pantallas blancas puras.
- **Surface (`#FFFFFF`)**: Blanco puro para contenedores de tarjetas, paneles del configurador, modales y tablas de despiece técnico.
- **Surface Alt (`#F0F4F8`)**: Gris azulado tenue para cabeceras de tablas técnicas, ranuras de tablero vacías y filas alternadas.
- **Border (`#C8D0D8`)**: Gris medio para divisores de ranuras y marcos de tarjetas.

---

## 3. Typography

La tipografía utiliza fuentes de sistema robustas para garantizar rendimiento instantáneo, complementadas con fuentes monoespaciadas para precisión técnica:

### 3.1 Jerarquía Tipográfica
- **Display (`clamp(1.75rem, 3.5vw, 2.25rem)`, Bold 800)**: Títulos principales de flujo (ej. "Configurador Técnico de Tableros", "Cotización de Materiales").
- **Headline / H2 (`1.5rem`, Bold 700)**: Títulos de sección (ej. "Gabinete Anfitrión", "Derivados Instalados", "Lista de Materiales BOM").
- **Title / H3 (`1.125rem`, Bold 700)**: Nombres de producto en tarjetas técnicas y títulos de bloques.
- **Body (`0.95rem`, Regular 400, Line Height 1.5)**: Descripciones técnicas y notas de aplicación.
- **Technical Code / SKUs (`0.85rem`, Semibold 600, Monospace)**: Números de parte, códigos de fabricante (`TAB-NQ-225`, `INT-QO-120`) y designaciones de ranura/polo (`Polo 1-3`, `20A 1P`).
- **Badge / Label (`0.85rem`, Semibold 600)**: Etiquetas de estado (`DRAFT`, `VALIDATED`), número de polos y compatibilidad.

---

## 4. Layout

El sistema se estructura en dos vistas de trabajo fundamentales dentro de un contenedor centrado con navegación fija:

### 4.1 Grid de la Vista Comercial Rápida (`/quotes/new/`)
- **Columna Principal (65%)**: Catálogo interactivo de componentes con filtro rápido y buscador por texto/SKU.
- **Columna Lateral Fija (35%)**: Resumen de partidas agregadas, sugerencias de accesorios vinculados (`COMPLEMENT_OF`) y botón de confirmación de lista técnica.

### 4.2 Layout del Configurador de Tableros (`/quotes/<id>/configurator/`)
- **Panel Superior**: Ficha del tablero anfitrión (SKU, nombre, capacidad total de polos y amperaje de barras).
- **Barra de Ocupación Dinámica**: Indicador visual continuo de capacidad:
  - Verde: Capacidad con holgura ($< 80\%$).
  - Amarillo: Capacidad cercana al límite ($80\% - 100\%$).
  - Rojo: Sobrecupo ($> 100\%$) con bloqueo del botón de validación.
- **Esquema de Ranuras (Chasis 2D)**: Representación de las ranuras del tablero en dos columnas (pares e impares) reflejando el orden físico real de montaje.
- **Sección Inferior**: Tabla de despiece de materiales (*BOM*) generada con selector de descarga / impresión.

---

## 5. Elevation & Depth

La elevación transmite jerarquía industrial limpia sin sombras excesivas ni efectos flotantes irreales:

- **Plano Base (Nivel 0)**: Fondo `#E6E8E5`.
- **Paneles y Tarjetas (Nivel 1)**: `box-shadow: 0 4px 12px rgba(0, 0, 0, 0.07); background: #FFFFFF; border: 1px solid #C8D0D8;`.
- **Ranuras del Chasis (Nivel Hueco/Inset)**: `box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1); background: #F0F4F8;` para ranuras vacías; fondo `#FFFFFF` con borde `#007BFF` para ranuras ocupadas.
- **Modales y Diálogos Flotantes (Nivel 3)**: `box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25); border-radius: 12px;`.

---

## 6. Shapes

- **Radios de Borde**:
  - `sm (4px)`: Badges de polos (`1P`, `3P`), etiquetas de voltaje, chips de SKU.
  - `md (8px)`: Botones de acción, campos de entrada, ranuras de montaje en chasis.
  - `lg (12px)`: Tarjetas de producto, contenedores de paneles, modal de despiece.
  - `full (9999px)`: Píldoras de estado (`VALIDADO`, `BORRADOR`), indicadores de porcentaje de capacidad.

---

## 7. Components

### 7.1 Botones
- **Primario (`button-primary`)**: Fondo `#1E1E1E`, texto blanco, esquinas `8px`. Para guardar, avanzar o confirmar.
- **Acento (`button-accent`)**: Fondo `#007BFF`, texto blanco. Para agregar derivado, seleccionar gabinete.
- **Éxito (`button-success`)**: Fondo `#28A745`, texto blanco. Para validar configuración y generar BOM.
- **Secundario / Outline**: Fondo transparente, borde `1px solid #1E1E1E`, texto `#1E1E1E`.

### 7.2 Indicador de Ranuras y Polos (Slot Bar)
Componente reactivo impulsado por Alpine.js:
- Muestra `Polos ocupados / Capacidad total` (ej. `18 / 30 Polos`).
- Barra de progreso con transición fluida (`transition: width 0.3s ease`).
- Mensaje reactivo que informa los espacios restantes o alerta de sobrecupo.

### 7.3 Tarjeta de Componente
- Encabezado con SKU monoespaciado en negrita y tipo (`COMPONENT` o `ACCESSORY`).
- Atributos clave en chips: Polos, Amperaje nominal, Tipo de montaje (`enchufable` / `atornillable`).
- Selector de cantidad rápido con botones `+` y `-`.
- Enlace directo a "Accesorios compatibles" desplegable.

### 7.4 Tabla de Lista de Materiales (BOM)
- Encabezado oscuro con tipografía contrastada.
- Columnas: Posición / Ranura, Código SKU, Descripción Oficial, Tipo, Cantidad y Notas de Montaje.
- Filas alternadas en `#FFFFFF` y `#F0F4F8`.
- Sin columnas de precios, costos ni subtotales monetarios.

---

## 8. Do's and Don'ts

### Do's ✅
- **Hacer**: Mantener siempre visibles los códigos SKU y atributos técnicos (polos, amperaje) en fuentes monoespaciadas legibles.
- **Hacer**: Explicar con claridad meridiana el motivo exacto de una incompatibilidad (ej. "Faltan 2 espacios en el tablero para alojar este interruptor").
- **Hacer**: Proporcionar retroalimentación inmediata en el navegador al agregar o retirar piezas antes de emitir la validación formal en el backend.
- **Hacer**: Usar el logotipo SVG corporativo oficial (`abv sin fondo.svg`) y respetar el esquema de color industrial de ABV Electric Supply.

### Don'ts ❌
- **No hacer**: No incluir columnas de precios, monedas, subtotales ni símbolos de pesos (`$`) en ningún formulario, tarjeta o tabla.
- **No hacer**: No permitir que el usuario confunda un accesorio recomendado (`COMPLEMENT_OF`) con un requisito obligatorio que bloquee el ensamble (`REQUIRES`).
- **No hacer**: No usar animaciones lentas o decorativas que entorpezcan la rapidez operativa de un ingeniero o contratista en obra.
- **No hacer**: No delegar la validación física exclusivamente al cliente JavaScript; el servidor Django siempre debe re-validar el ensamble antes de emitir la BOM.
