# Technical Contract: Generación de Lista de Materiales (BOM)

Especificación del formato estructurado para el despiece técnico (*Bill of Materials* - BOM) emitido por el selector `get_quote_bom(quote)`.

---

## 1. Estructura de Salida del BOM

El selector retorna un diccionario/objeto estructurado con las siguientes secciones:

```json
{
  "header": {
    "quote_id": 105,
    "folio": "COT-2026-0042",
    "client_name": "Ingeniería y Fuerza del Bajío",
    "project_reference": "Planta Ensambladora Lote 4",
    "status": "VALIDATED",
    "generated_at": "2026-10-21T11:40:00Z"
  },
  "enclosure": {
    "sku": "TAB-NQ-225",
    "name": "Tablero Alumbrado NQ 225A 30 Polos",
    "quantity": 1,
    "specs": {
      "espacios": 30,
      "amperaje_max": 225,
      "fases": 3
    }
  },
  "branch_breakers": [
    {
      "sku": "INT-QO-120",
      "name": "Interruptor Termomagnético QO 1P 20A",
      "quantity": 12,
      "poles_per_unit": 1,
      "total_poles": 12,
      "mounting": "enchufable",
      "slots_assigned": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    },
    {
      "sku": "INT-EDB-3100",
      "name": "Interruptor Termomagnético EDB 3P 100A",
      "quantity": 2,
      "poles_per_unit": 3,
      "total_poles": 6,
      "mounting": "atornillable",
      "slots_assigned": [13, 15, 17, 14, 16, 18]
    }
  ],
  "accessories_and_kits": [
    {
      "sku": "KIT-ZAP-225",
      "name": "Kit Zapata Neutro 225A Aluminio",
      "quantity": 1,
      "associated_to": "TAB-NQ-225",
      "notes": "Barras de neutro y tierra"
    },
    {
      "sku": "ACC-AUX-QO",
      "name": "Contacto Auxiliar 1NA/1NC para QO",
      "quantity": 2,
      "associated_to": "INT-QO-120",
      "notes": "Montaje lateral izquierdo en interruptores 1 y 2"
    }
  ],
  "totals": {
    "total_slots_capacity": 30,
    "total_slots_occupied": 18,
    "total_slots_available": 12,
    "total_unique_skus": 4,
    "total_physical_items": 16
  }
}
```

---

## 2. Invariantes de Calidad del BOM
1. **Conservación de cantidades**: La suma de cantidades de cada partida en el BOM coincide exactamente con la suma agregada de las partidas registradas en `QuoteItem`.
2. **Exactitud de SKUs**: Ningún SKU es generado al vuelo o truncado; todos provienen de registros activos en `Product`.
3. **Reproducibilidad**: Una cotización en estado `VALIDATED`, `SENT` o `ACCEPTED` generará siempre exactamente el mismo BOM mientras no sea revertida a `DRAFT`.
