# Contract: Catalog & Compatibility Graph REST API

**Interface**: OpenAPI 3.1.0 / Django Ninja REST Service  
**Base Path**: `/api/v1/catalog`  
**Data Format**: JSON (application/json)  

---

## 1. Endpoints

### 1.1 Listar Productos
- **Ruta**: `GET /api/v1/catalog/products/`
- **Parámetros de Consulta**:
  - `product_type` (opcional): Filtro por enum (`BOARD`, `COMPONENT`, `ACCESSORY`).
  - `search` (opcional): Búsqueda por coincidencia en `sku` o `name`.
  - `limit` (opcional, default 50): Límite de paginación.
  - `offset` (opcional, default 0): Desplazamiento.

#### Respuesta Exitosa (200 OK)
```json
{
  "count": 5,
  "items": [
    {
      "id": 1,
      "sku": "TAB-NQ-225",
      "name": "Tablero Alumbrado NQ 225A 30 Polos",
      "slug": "tab-nq-225",
      "product_type": "BOARD",
      "specs": {
        "espacios": 30,
        "amperaje_max": 225,
        "fases": 3
      },
      "is_active": true
    }
  ]
}
```

---

### 1.2 Detalle de Producto
- **Ruta**: `GET /api/v1/catalog/products/{sku}/`
- **Respuesta 200 OK**: Objeto de producto completo con `specs` y timestamps.
- **Respuesta 404 Not Found**: `{"detail": "Product with SKU '{sku}' not found"}`.

---

### 1.3 Compatibilidades Directas
- **Ruta**: `GET /api/v1/catalog/products/{sku}/compatibilities/`
- **Parámetros de Consulta**:
  - `relationship_type` (opcional): Filtro por tipo (`COMPATIBLE_WITH`, `COMPLEMENT_OF`, `REQUIRES`, `ALTERNATIVE_TO`).

#### Respuesta Exitosa (200 OK)
```json
{
  "product": {
    "sku": "TAB-NQ-225",
    "name": "Tablero Alumbrado NQ 225A 30 Polos"
  },
  "compatibilities": [
    {
      "target_sku": "INT-QO-120",
      "target_name": "Interruptor Termomagnético QO 1P 20A",
      "target_type": "COMPONENT",
      "relationship_type": "COMPATIBLE_WITH",
      "score": 100,
      "notes": "Hasta 30 circuitos en total",
      "specs": {
        "polos": 1,
        "amperaje": 20,
        "montaje": "enchufable"
      }
    },
    {
      "target_sku": "KIT-ZAP-225",
      "target_name": "Kit Zapata Neutro 225A Aluminio",
      "target_type": "ACCESSORY",
      "relationship_type": "COMPLEMENT_OF",
      "score": 90,
      "notes": "Opcional para barras de neutro",
      "specs": {
        "material": "aluminio",
        "calibre": "4-300 kcmil"
      }
    }
  ]
}
```

---

### 1.4 Árbol de Cotización Completo (Sin N+1 Queries)
- **Ruta**: `GET /api/v1/catalog/products/{sku}/tree/`
- **Descripción**: Resuelve en una única llamada (y exactamente 2 consultas SQL en backend) el producto anfitrión, todos sus componentes compatibles y los accesorios asociados a cada componente.

#### Respuesta Exitosa (200 OK)
```json
{
  "sku": "TAB-NQ-225",
  "name": "Tablero Alumbrado NQ 225A 30 Polos",
  "product_type": "BOARD",
  "specs": {"espacios": 30, "amperaje_max": 225},
  "compatible_components": [
    {
      "sku": "INT-QO-120",
      "name": "Interruptor Termomagnético QO 1P 20A",
      "relationship_type": "COMPATIBLE_WITH",
      "score": 100,
      "accessories": [
        {
          "sku": "ACC-AUX-QO",
          "name": "Contacto Auxiliar 1NA/1NC para QO",
          "relationship_type": "COMPLEMENT_OF",
          "score": 100,
          "notes": "Montaje lateral izquierdo"
        }
      ]
    }
  ],
  "direct_accessories": [
    {
      "sku": "KIT-ZAP-225",
      "name": "Kit Zapata Neutro 225A Aluminio",
      "relationship_type": "COMPLEMENT_OF",
      "score": 90
    }
  ]
}
```
