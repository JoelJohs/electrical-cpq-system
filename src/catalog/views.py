"""Vistas web para la consulta y exploración de compatibilidades técnicas."""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from catalog.models import Product
from catalog.selectors import get_product_compatibility_tree


def explorer_view(request: HttpRequest) -> HttpResponse:
    """Vista principal para la selección y exploración de compatibilidades."""
    total_products = Product.objects.filter(is_active=True).count()
    products = Product.objects.filter(is_active=True).order_by("nombre_corto")[:50]
    return render(
        request,
        "catalog/explorer.html",
        {
            "products": products,
            "total_products": total_products,
        },
    )


def product_tree_json_view(request: HttpRequest, product_id: int) -> JsonResponse:
    """Endpoint JSON rápido para el árbol de compatibilidades."""
    tree = get_product_compatibility_tree(product_id)
    if not tree:
        return JsonResponse({"error": "Producto no encontrado"}, status=404)
    return JsonResponse(tree)
