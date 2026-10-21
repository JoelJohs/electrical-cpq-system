# Quickstart & Validation Guide: Flujo Principal de Configuración y Cotizaciones Técnicas (Fase 4 - Happy Path)

Esta guía describe los escenarios reproducibles para validar el funcionamiento integral del Happy Path técnico sin precios monetarios.

---

## 1. Prerrequisitos

Asegúrate de contar con el entorno virtual activo y el catálogo eléctrico semilla cargado:

```bash
# 1. Aplicar migraciones
uv run python manage.py migrate

# 2. Cargar catálogo semilla (Tablero NQ, interruptores QO/EDB y accesorios)
uv run python manage.py seed_electrical_catalog
```

---

## 2. Escenario 1: Flujo Completo del Happy Path vía API / Shell

### Paso A: Crear una Cotización para Tablero NQ
```bash
curl -X POST http://127.0.0.1:8000/api/v1/quotes/ \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Constructora Electro Bajío",
    "project_reference": "Nave Industrial Módulo A",
    "is_board_assembly": true,
    "board_sku": "TAB-NQ-225"
  }'
```
*Resultado esperado*: HTTP 201 con folio generado (ej. `COT-2026-0001`) y estado `DRAFT`.

### Paso B: Agregar 10 Interruptores QO 1P 20A (10 espacios)
```bash
curl -X POST http://127.0.0.1:8000/api/v1/quotes/1/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_sku": "INT-QO-120",
    "quantity": 10
  }'
```
*Resultado esperado*: HTTP 201 con partida agregada.

### Paso C: Validar la Configuración
```bash
curl -X POST http://127.0.0.1:8000/api/v1/quotes/1/validate/
```
*Resultado esperado*:
```json
{
  "valid": true,
  "summary": {
    "total_slots_capacity": 30,
    "occupied_slots": 10,
    "available_slots": 20
  },
  "errors": [],
  "suggested_accessories": [
    { "sku": "KIT-ZAP-225", "relationship_type": "COMPLEMENT_OF" }
  ]
}
```

### Paso D: Generar la Lista de Materiales (BOM)
```bash
curl -s http://127.0.0.1:8000/api/v1/quotes/1/bom/ | jq .
```
*Resultado esperado*: Despiece técnico con 1 Tablero NQ, 10 interruptores QO y total de partes consolidado.

---

## 3. Escenario 2: Detección de Sobrecupo Físico (Error Controlado)

Intentar agregar 25 interruptores adicionales (total 35 polos > 30 disponibles):
```bash
curl -X POST http://127.0.0.1:8000/api/v1/quotes/1/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_sku": "INT-QO-120",
    "quantity": 25
  }'

curl -X POST http://127.0.0.1:8000/api/v1/quotes/1/validate/
```
*Resultado esperado*:
```json
{
  "valid": false,
  "errors": [
    {
      "code": "INSUFFICIENT_SPACE",
      "message": "La suma de polos de los componentes derivados (35) excede la capacidad física del tablero (30).",
      "details": {
        "required_spaces": 35,
        "available_spaces": 30,
        "overflow": 5
      }
    }
  ]
}
```

---

## 4. Escenario 3: Interfaz Web Asistida (Django Templates + Tailwind + Alpine.js)

1. Iniciar servidor de desarrollo:
   ```bash
   uv run python manage.py runserver
   ```
2. Acceder en el navegador:
   - Vista Comercial: `http://127.0.0.1:8000/quotes/new/`
   - Configurador de Tableros: `http://127.0.0.1:8000/quotes/1/configurator/`
3. Probar interactividad:
   - Al mover el control de cantidad de interruptores, el indicador visual de ocupación de ranuras se actualiza en tiempo real con Alpine.js.
   - Si se supera el límite de 30 polos, la barra se pinta en color rojo con mensaje de advertencia.
   - Al pulsar "Validar y Generar BOM", HTMX realiza la llamada asíncrona al backend y despliega la tabla de materiales lista para exportar/imprimir.
