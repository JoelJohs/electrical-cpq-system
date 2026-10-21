# Arquitectura del Grafo de Catálogo Eléctrico

Este documento describe la arquitectura de datos, el modelo de grafo relacional en PostgreSQL/Django, las capas modulares y los endpoints de consulta del catálogo de productos eléctricos del sistema CPQ.

---

## 1. Modelo Conceptual: Grafo Dirigido en SQL

En el sector eléctrico industrial y comercial, los catálogos técnicos no son colecciones planas de artículos, sino **grafos dirigidos acíclicos o redes de compatibilidad física y eléctrica**:

```text
  [ Tablero NQ (BOARD) ] ────────(COMPATIBLE_WITH)───────▶ [ Interruptor QO 20A (COMPONENT) ]
        │                                                                │
        │                                                                │
 (COMPLEMENT_OF)                                                  (COMPLEMENT_OF)
        │                                                                │
        ▼                                                                ▼
[ Kit Zapata Neutro (ACCESSORY) ]                                [ Contacto Auxiliar OF (ACCESSORY) ]
```

### ¿Por qué evitar `is_bidirectional = BooleanField`?
1. **Asimetría física estricta**: Un *Tablero NQ* aloja un *Interruptor QO*, pero un interruptor jamás aloja un tablero. Un interruptor recibe una *bobina de disparo*, pero la bobina no aloja al interruptor. Una bandera bidireccional provocaría que al consultar accesorios de una bobina, el sistema sugiera el interruptor y el tablero completo.
2. **Eficiencia en ORM y base de datos**: Forzar consultas bidireccionales con uniones de conjuntos (`.union()`) anula optimizaciones nativas de Django como `select_related`, `prefetch_related` y paginación determinista sobre QuerySets.

---

## 2. Tipos de Entidades y Semántica de Relación

### Tipos de Producto (`ProductType`)
* `BOARD`: Gabinete, panel o tablero eléctrico contenedor.
* `COMPONENT`: Componente principal activo (interruptores termomagnéticos, contactores, variadores).
* `ACCESSORY`: Accesorio mecánico o eléctrico secundario (kits de zapatas, contactos auxiliares, bobinas de disparo).

### Semántica de Relación (`RelationshipType`)
* `COMPATIBLE_WITH`: Relación de montaje físico o alojamiento principal (ej. Tablero aloja Interruptor).
* `COMPLEMENT_OF`: Accesorio o complemento directo del producto origen.
* `REQUIRES`: Dependencia técnica obligatoria (el producto origen no opera sin el producto destino).
* `ALTERNATIVE_TO`: Sustituto funcional directo o reemplazo técnico.

---

## 3. Integridad en Base de Datos e Índices Compuestos

En `src/catalog/models.py`, la persistencia se divide en:
1. **Nodos (`Product`)**:
   - `sku` (único, indexado)
   - `name`, `slug` (único)
   - `product_type` (`BOARD`, `COMPONENT`, `ACCESSORY`, indexado)
   - `specs` (`JSONField` nativo para atributos técnicos: polos, amperaje, tensión, montaje)
   - `is_active` (filtro rápido)
2. **Aristas (`ProductCompatibility`)**:
   - `source` (`ForeignKey` hacia `Product`, producto anfitrión)
   - `target` (`ForeignKey` hacia `Product`, producto compatible/accesorio)
   - `relationship_type` (tipo de arista)
   - `score` (prioridad de recomendación numérica)
   - `notes` (notas de montaje)

### Restricciones DB
* `prevent_self_relation`: `CheckConstraint(condition=~models.Q(source=models.F("target")), name="prevent_self_relation")` — ningún producto puede relacionarse consigo mismo a nivel de motor SQL.
* `unique_source_target_rel_type`: `UniqueConstraint(fields=["source", "target", "relationship_type"])` — previene duplicación exacta de aristas.

### Índices B-Tree Compuestos
* `Index(fields=["source", "relationship_type"])`
* `Index(fields=["target", "relationship_type"])`
Garantizan que las búsquedas jerárquicas o en cascada se resuelvan en sub-milisegundos vía Index Scan en PostgreSQL.

---

## 4. Capas de la Arquitectura Modular

Siguiendo el principio de separación de responsabilidades y modularidad limpia:

```text
src/catalog/
├── models.py       # Dominio y reglas de integridad en DB
├── enums.py        # TextChoices de dominio (ProductType, RelationshipType)
├── selectors.py    # Consultas de lectura optimizadas (evitan N+1)
├── schemas.py      # Esquemas Pydantic v2 para validación y serialización
├── api.py          # Endpoints REST montados en Django Ninja
├── admin.py        # Gobernanza administrativa con Inlines
└── tests/          # Pruebas automatizadas (modelos, selectores, api, admin)
```

### Capa de Selectores (`selectors.py`)
Para evitar el problema de $N+1$ queries en árboles de compatibilidad:
- `get_product_compatibility_tree(sku)` resuelve el producto raíz, todos sus componentes compatibles y todos sus accesorios en **exactamente 2 consultas SQL fijas**, independientemente del volumen de aristas, utilizando `prefetch_related(Prefetch(...))`.

---

## 5. Datos Semilla y Comandos de Gestión

Para poblar el catálogo con ejemplos de demostración validados técnicamente:

```bash
uv run python manage.py seed_electrical_catalog
```

Este comando carga:
- `TAB-NQ-225`: Tablero Alumbrado NQ 225A 30 Polos (BOARD)
- `INT-QO-120`: Interruptor QO 1P 20A (COMPONENT)
- `INT-EDB-3100`: Interruptor EDB 3P 100A (COMPONENT)
- `ACC-AUX-QO`: Contacto Auxiliar 1NA/1NC para QO (ACCESSORY)
- `KIT-ZAP-225`: Kit Zapata Neutro 225A (ACCESSORY)
Y configura las aristas correspondientes sin relaciones circulares.

---

## 6. Endpoints REST (Django Ninja)

La API REST está montada en el prefijo `/api/` y documentada automáticamente con Swagger / OpenAPI en `/api/docs`.

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/products/` | Lista paginada y filtrable por `product_type` y `is_active` |
| `GET` | `/api/products/{sku}/` | Ficha técnica detallada de un producto por SKU |
| `GET` | `/api/products/{sku}/tree/` | Árbol completo de compatibilidad (componentes y accesorios anidados) |
| `GET` | `/api/compatibilities/` | Lista de aristas filtrables por `source_sku` o `relationship_type` |

### Ejemplo: Consulta del Árbol de Compatibilidad
`GET /api/products/TAB-NQ-225/tree/`
```json
{
  "product": {
    "sku": "TAB-NQ-225",
    "name": "Tablero Alumbrado NQ 225A 30 Polos",
    "product_type": "BOARD",
    "specs": { "espacios": 30, "amperaje_max": 225, "fases": 3 }
  },
  "compatible_components": [
    {
      "sku": "INT-QO-120",
      "name": "Interruptor Termomagnético QO 1P 20A",
      "product_type": "COMPONENT",
      "relationship_type": "COMPATIBLE_WITH",
      "score": 100
    }
  ],
  "accessories": [
    {
      "sku": "KIT-ZAP-225",
      "name": "Kit Zapata Neutro 225A Aluminio",
      "product_type": "ACCESSORY",
      "relationship_type": "COMPLEMENT_OF",
      "score": 90
    }
  ]
}
```

---

## 7. Base de Datos Local vs. Producción (VPS)

Para desarrollo local rápido y reproducible sin alterar el sistema operativo anfitrión:
- Se provee un contenedor PostgreSQL 17 desechable en `docker-compose.yml`.
- Se gestiona mediante el script auxiliar `scripts/db_dev.sh`:
  - `./scripts/db_dev.sh up`: Inicia el contenedor PostgreSQL 17 en segundo plano.
  - `./scripts/db_dev.sh down`: Detiene el contenedor.
  - `./scripts/db_dev.sh status`: Verifica el estado de conexión del contenedor.
  - `./scripts/db_dev.sh reset`: Limpia volúmenes y recrea la base de datos limpia.
- La aplicación se desacopla mediante `DATABASE_URL` en `.env`. Si no se define o si PostgreSQL no está levantado, el sistema conmuta a SQLite local de manera transparente para pruebas unitarias.
