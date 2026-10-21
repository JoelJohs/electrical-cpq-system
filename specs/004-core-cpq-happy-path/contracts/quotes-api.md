# API Contract: Endpoints de Cotizaciones Técnicas y Configurador

Documentación de contratos REST implementados mediante Django Ninja en el prefijo `/api/v1/quotes/`.

---

## 1. `POST /api/v1/quotes/` (Crear Cotización Técnica)

Crea una nueva cotización técnica o ensamble de tablero en estado `DRAFT`.

### Request Body (`CreateQuoteSchema`)
```json
{
  "client_name": "Constructora Eléctrica del Centro S.A. de C.V.",
  "project_reference": "Obra Torre Financiera Nivel 3",
  "is_board_assembly": true,
  "board_sku": "TAB-NQ-225",
  "notes": "Alimentación 220V 3F 4H"
}
```

### Response 201 Created (`QuoteDetailSchema`)
```json
{
  "id": 1,
  "folio": "COT-2026-0001",
  "client_name": "Constructora Eléctrica del Centro S.A. de C.V.",
  "project_reference": "Obra Torre Financiera Nivel 3",
  "status": "DRAFT",
  "is_board_assembly": true,
  "board": {
    "sku": "TAB-NQ-225",
    "name": "Tablero Alumbrado NQ 225A 30 Polos",
    "specs": { "espacios": 30, "amperaje_max": 225, "fases": 3 }
  },
  "items": [],
  "notes": "Alimentación 220V 3F 4H",
  "created_at": "2026-10-21T11:30:00Z",
  "updated_at": "2026-10-21T11:30:00Z"
}
```

---

## 2. `POST /api/v1/quotes/{id}/items/` (Agregar Partida a Cotización)

Agrega un producto del catálogo como partida a una cotización en estado editable.

### Request Body (`AddQuoteItemSchema`)
```json
{
  "product_sku": "INT-QO-120",
  "quantity": 10,
  "slot_position": 1,
  "notes": "Circuitos de alumbrado pasillos"
}
```

### Response 201 Created (`QuoteItemSchema`)
```json
{
  "id": 15,
  "product_sku": "INT-QO-120",
  "product_name": "Interruptor Termomagnético QO 1P 20A",
  "product_type": "COMPONENT",
  "quantity": 10,
  "slot_position": 1,
  "notes": "Circuitos de alumbrado pasillos"
}
```

### Errores Comunes
- `404 Not Found`: Cotización o producto no encontrado.
- `409 Conflict`: La cotización se encuentra en estado de solo lectura (`SENT`, `ACCEPTED`, `CANCELLED`).

---

## 3. `DELETE /api/v1/quotes/{id}/items/{item_id}/` (Eliminar Partida)

Elimina una partida de una cotización editable.

### Response 200 OK
```json
{
  "success": true,
  "message": "Partida eliminada correctamente",
  "quote_id": 1
}
```

---

## 4. `POST /api/v1/quotes/{id}/validate/` (Validar Configuración Técnica)

Ejecuta el motor de validación de reglas sobre todas las partidas de la cotización y evalúa la viabilidad técnica.

### Response 200 OK (Configuración Válida)
```json
{
  "valid": true,
  "quote_id": 1,
  "folio": "COT-2026-0001",
  "summary": {
    "total_slots_capacity": 30,
    "occupied_slots": 10,
    "available_slots": 20,
    "max_amperage_capacity": 225,
    "highest_component_amperage": 20
  },
  "errors": [],
  "suggested_accessories": [
    {
      "sku": "KIT-ZAP-225",
      "name": "Kit Zapata Neutro 225A Aluminio",
      "relationship_type": "COMPLEMENT_OF",
      "target_for_sku": "TAB-NQ-225",
      "notes": "Opcional para barras de tierra"
    }
  ]
}
```

### Response 200 OK (Configuración Inválida con Errores Estructurados)
```json
{
  "valid": false,
  "quote_id": 1,
  "folio": "COT-2026-0001",
  "summary": {
    "total_slots_capacity": 30,
    "occupied_slots": 32,
    "available_slots": 0,
    "overflow_slots": 2
  },
  "errors": [
    {
      "code": "INSUFFICIENT_SPACE",
      "message": "La suma de polos de los componentes derivados (32) excede la capacidad física del tablero (30).",
      "details": {
        "required_spaces": 32,
        "available_spaces": 30,
        "overflow": 2
      }
    },
    {
      "code": "MISSING_REQUIRED_ACCESSORY",
      "message": "El componente INT-QO-120 exige obligatoriamente el accesorio ACC-AUX-QO para su instalación.",
      "details": {
        "source_sku": "INT-QO-120",
        "required_target_sku": "ACC-AUX-QO"
      }
    }
  ],
  "suggested_accessories": []
}
```

---

## 5. `GET /api/v1/quotes/{id}/bom/` (Obtener Lista de Materiales - BOM)

Genera el despiece estructurado de materiales listo para taller de ensamble o almacén.

### Response 200 OK (`BOMResponseSchema`)
```json
{
  "quote_id": 1,
  "folio": "COT-2026-0001",
  "client_name": "Constructora Eléctrica del Centro S.A. de C.V.",
  "project_reference": "Obra Torre Financiera Nivel 3",
  "is_validated": true,
  "generated_at": "2026-10-21T11:45:00Z",
  "board": {
    "sku": "TAB-NQ-225",
    "name": "Tablero Alumbrado NQ 225A 30 Polos",
    "quantity": 1
  },
  "components": [
    {
      "sku": "INT-QO-120",
      "name": "Interruptor Termomagnético QO 1P 20A",
      "quantity": 10,
      "poles_per_unit": 1,
      "total_poles": 10
    }
  ],
  "accessories": [
    {
      "sku": "ACC-AUX-QO",
      "name": "Contacto Auxiliar 1NA/1NC para QO",
      "quantity": 2,
      "target_for_sku": "INT-QO-120"
    }
  ],
  "total_unique_items": 3,
  "total_parts_count": 13
}
```
