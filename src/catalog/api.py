"""API REST de catálogo y compatibilidades eléctricas con Django Ninja."""

from typing import Optional

from django.http import Http404
from ninja import NinjaAPI, Router

from catalog.schemas import (
    ProductCompatibilitiesResponse,
    ProductListResponse,
    ProductSchema,
    ProductTreeResponse,
)
from catalog.selectors import (
    get_product_by_id,
    get_product_compatibilities,
    get_product_compatibility_tree,
    list_active_products,
)

api = NinjaAPI(
    title="Electrical CPQ Compatibility API",
    version="1.0.0",
    description="API de catálogo y grafo de compatibilidades eléctricas",
    docs_url="/docs",
)

catalog_router = Router(tags=["Catálogo y Compatibilidades"])


@catalog_router.get("/products/", response=ProductListResponse)
def list_products(
    request,
    search: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Lista productos activos con búsqueda y filtro por categoría."""
    qs = list_active_products(search=search, category=category)
    total = qs.count()
    items = list(qs[offset : offset + limit])
    return {
        "total": total,
        "items": [
            {
                "id": p.id,
                "nombre_corto": p.nombre_corto,
                "nombre_largo": p.nombre_largo,
                "descripcion": p.descripcion,
                "is_active": p.is_active,
                "category": p.category,
            }
            for p in items
        ],
    }


@catalog_router.get("/products/{int:product_id}/", response=ProductSchema)
def get_product(request, product_id: int):
    """Obtiene el detalle de un producto por su ID."""
    product = get_product_by_id(product_id)
    if not product:
        raise Http404(f"Producto con ID {product_id} no encontrado")
    return {
        "id": product.id,
        "nombre_corto": product.nombre_corto,
        "nombre_largo": product.nombre_largo,
        "descripcion": product.descripcion,
        "is_active": product.is_active,
        "category": product.category,
    }


@catalog_router.get(
    "/products/{int:product_id}/compatibilities/",
    response=ProductCompatibilitiesResponse,
)
def list_compatibilities(
    request,
    product_id: int,
    relationship_type: Optional[str] = None,
):
    """Lista las compatibilidades y relaciones salientes de un producto."""
    product = get_product_by_id(product_id)
    if not product:
        raise Http404(f"Producto con ID {product_id} no encontrado")

    edges = get_product_compatibilities(product_id, relationship_type=relationship_type)
    formatted_edges = [
        {
            "id": edge.id,
            "target_id": edge.target.id,
            "target_nombre_corto": edge.target.nombre_corto,
            "target_nombre_largo": edge.target.nombre_largo,
            "relationship_type": edge.relationship_type,
            "score": edge.score,
            "notes": edge.notes,
        }
        for edge in edges
    ]

    return {
        "product": {
            "id": product.id,
            "nombre_corto": product.nombre_corto,
            "nombre_largo": product.nombre_largo,
            "descripcion": product.descripcion,
            "is_active": product.is_active,
        },
        "compatibilities": formatted_edges,
    }


@catalog_router.get("/products/{int:product_id}/tree/", response=ProductTreeResponse)
def get_tree(request, product_id: int):
    """Obtiene árbol de componentes compatibles, requeridos y alternativos."""
    tree = get_product_compatibility_tree(product_id)
    if not tree:
        raise Http404(f"Producto con ID {product_id} no encontrado")
    return tree


api.add_router("/v1/catalog", catalog_router)
