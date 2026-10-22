"""Vistas web para la consulta y exploración de compatibilidades técnicas."""

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from catalog.models import Product
from catalog.selectors import get_product_compatibility_tree


def explorer_view(request: HttpRequest) -> HttpResponse:
    """Vista principal para la selección y exploración de compatibilidades."""
    version = cache.get("catalog:cache_version", 1)
    total_key = f"catalog:v{version}:total_active"
    initial_key = f"catalog:v{version}:initial_50"

    total_products = cache.get(total_key)
    if total_products is None:
        total_products = Product.objects.filter(is_active=True).count()
        cache.set(total_key, total_products, timeout=1800)

    products = cache.get(initial_key)
    if products is None:
        products = list(
            Product.objects.filter(is_active=True).order_by("nombre_corto")[:50]
        )
        cache.set(initial_key, products, timeout=1800)

    return render(
        request,
        "catalog/explorer.html",
        {
            "products": products,
            "total_products": total_products,
        },
    )


def product_tree_json_view(request: HttpRequest, product_id: int) -> JsonResponse:
    """Endpoint JSON rápido para el árbol de compatibilidades con cabeceras de caché."""
    tree = get_product_compatibility_tree(product_id)
    if not tree:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)
    response = JsonResponse(tree)
    response["Cache-Control"] = "public, max-age=120, stale-while-revalidate=300"
    return response
