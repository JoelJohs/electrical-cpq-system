from typing import Optional

from django.db.models import Q
from django.http import Http404
from ninja import NinjaAPI, Router

from catalog.models import Product
from catalog.schemas import (
    CompatibilityEdgeSchema,
    ProductCompatibilitiesResponse,
    ProductListResponse,
    ProductSchema,
    ProductTreeResponse,
)
from catalog.selectors import (
    get_product_by_sku,
    get_product_compatibilities,
    get_product_compatibility_tree,
)

api = NinjaAPI(
    title="Electrical CPQ Catalog API",
    version="1.0.0",
    description="API de catálogo y grafo de compatibilidades eléctricas",
    docs_url="/docs",
)

catalog_router = Router(tags=["Catálogo y Compatibilidades"])


@catalog_router.get("/products/", response=ProductListResponse)
def list_products(
    request,
    product_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Lista productos activos con filtros opcionales de tipo o término de búsqueda."""
    qs = Product.objects.filter(is_active=True).order_by("sku")

    if product_type:
        qs = qs.filter(product_type=product_type)

    if search:
        qs = qs.filter(Q(sku__icontains=search) | Q(name__icontains=search))

    total = qs.count()
    items = list(qs[offset : offset + limit])

    return {"count": total, "items": items}


@catalog_router.get("/products/{sku}/", response=ProductSchema)
def get_product(request, sku: str):
    """Obtiene el detalle completo de un producto por su SKU."""
    product = get_product_by_sku(sku)
    if not product:
        raise Http404(f"Producto con SKU '{sku}' no encontrado")
    return product


@catalog_router.get(
    "/products/{sku}/compatibilities/",
    response=ProductCompatibilitiesResponse,
)
def list_compatibilities(
    request,
    sku: str,
    relationship_type: Optional[str] = None,
):
    """
    Obtiene las aristas de compatibilidad directas donde el producto actúa
    como 'source'.
    """
    product = get_product_by_sku(sku)
    if not product:
        raise Http404(f"Producto con SKU '{sku}' no encontrado")

    edges = get_product_compatibilities(sku, relationship_type=relationship_type)

    formatted_edges = [
        CompatibilityEdgeSchema(
            target_sku=edge.target.sku,
            target_name=edge.target.name,
            target_type=edge.target.product_type,
            relationship_type=edge.relationship_type,
            score=edge.score,
            notes=edge.notes,
            specs=edge.target.specs,
        )
        for edge in edges
    ]

    return {
        "product": {"sku": product.sku, "name": product.name},
        "compatibilities": formatted_edges,
    }


@catalog_router.get("/products/{sku}/tree/", response=ProductTreeResponse)
def get_tree(request, sku: str):
    """
    Obtiene el árbol jerárquico completo para cotización (Anfitrión +
    Componentes + Accesorios) resuelto en exactamente 2 consultas SQL
    sin problema de N+1.
    """
    tree = get_product_compatibility_tree(sku)
    if not tree:
        raise Http404(f"Producto con SKU '{sku}' no encontrado")
    return tree


api.add_router("/v1/catalog", catalog_router)
