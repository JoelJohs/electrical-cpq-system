# Contract: Database Schema (PostgreSQL DDL & Constraints)

**Target Engines**: PostgreSQL 17 / PostgreSQL 16 (Compatible con SQLite en pruebas unitarias mediante ORM de Django)  
**App**: `catalog`  

---

## 1. DDL: Tabla `catalog_product`

```sql
CREATE TABLE catalog_product (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    product_type VARCHAR(20) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    specs JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX catalog_product_sku_idx ON catalog_product(sku);
CREATE INDEX catalog_product_product_type_idx ON catalog_product(product_type);
CREATE INDEX catalog_product_is_active_idx ON catalog_product(is_active);
CREATE INDEX catalog_product_specs_gin_idx ON catalog_product USING GIN (specs);
```

---

## 2. DDL: Tabla `catalog_productcompatibility`

```sql
CREATE TABLE catalog_productcompatibility (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES catalog_product(id) ON DELETE CASCADE,
    target_id BIGINT NOT NULL REFERENCES catalog_product(id) ON DELETE CASCADE,
    relationship_type VARCHAR(30) NOT NULL DEFAULT 'COMPATIBLE_WITH',
    score INTEGER NOT NULL DEFAULT 100,
    notes VARCHAR(255) NOT NULL DEFAULT '',
    
    -- Restricción de comprobación: evitar auto-relación
    CONSTRAINT prevent_self_relation CHECK (source_id <> target_id),
    
    -- Restricción de unicidad: evitar aristas idénticas duplicadas
    CONSTRAINT unique_source_target_rel_type UNIQUE (source_id, target_id, relationship_type)
);

-- Índices B-Tree compuestos para consultas en cascada en < 1ms
CREATE INDEX catalog_productcompat_source_rel_idx ON catalog_productcompatibility (source_id, relationship_type);
CREATE INDEX catalog_productcompat_target_rel_idx ON catalog_productcompatibility (target_id, relationship_type);
```
