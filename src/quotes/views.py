"""Controladores de vistas web para el configurador de tableros y CPQ."""

import json
from typing import Any

from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from catalog.enums import ProductType, RelationshipType
from catalog.models import Product, ProductCompatibility
from quotes.models import Quote
from quotes.rules import validate_quote_configuration
from quotes.selectors import (
    get_quote_bom,
    get_quote_items,
    get_quote_suggested_complements,
    list_quotes,
)
from quotes.services import (
    QuoteStateError,
    add_item_to_quote,
    create_quote,
    remove_quote_item,
    transition_quote_status,
)


def quote_list_view(request: HttpRequest) -> HttpResponse:
    """Lista todas las cotizaciones técnicas registradas."""
    quotes = list_quotes()
    return render(request, "quotes/quote_list.html", {"quotes": quotes})


@require_http_methods(["GET", "POST"])
def quick_quote_view(request: HttpRequest) -> HttpResponse:
    """Módulo comercial rápido de selección y cotización."""
    if request.method == "POST":
        client_name = request.POST.get("client_name", "").strip()
        project_reference = request.POST.get("project_reference", "").strip()
        is_board_assembly = request.POST.get("is_board_assembly") in (
            "on",
            "true",
            "1",
            True,
        )
        board_sku = request.POST.get("board_sku", "").strip() or None
        items_json = request.POST.get("items_json", "[]")

        quote = create_quote(
            client_name=client_name,
            project_reference=project_reference,
            is_board_assembly=is_board_assembly,
            board_sku=board_sku,
        )

        try:
            items_data = json.loads(items_json)
            for item in items_data:
                sku = item.get("sku")
                qty = int(item.get("quantity", 1))
                if sku:
                    add_item_to_quote(quote=quote, product_sku=sku, quantity=qty)
        except Exception:
            pass

        if is_board_assembly:
            return redirect(f"/quotes/{quote.id}/configurator/")
        return redirect(f"/quotes/{quote.id}/bom/")

    products = Product.objects.filter(is_active=True).order_by("product_type", "sku")
    return render(request, "quotes/quick_quote.html", {"products": products})


def configurator_view(request: HttpRequest, quote_id: int) -> HttpResponse:
    """Configurador técnico interactivo de tableros eléctricos para integradores."""
    quote = get_object_or_404(
        Quote.objects.select_related("board_product"), id=quote_id
    )
    items = get_quote_items(quote)
    validation = validate_quote_configuration(quote)

    # Chasis físico 2D de ranuras (Pares e Impares)
    total_slots = validation["summary"].get("total_slots_capacity", 0) or 30
    occupied_slots_map: dict[int, Any] = {}
    current_slot = 1
    for it in items:
        poles = int(
            (it.product.specs or {}).get("polos")
            or (it.product.specs or {}).get("espacios")
            or 1
        )
        start_slot = it.slot_position if it.slot_position else current_slot
        for offset in range(poles * it.quantity):
            slot_num = start_slot + offset
            if slot_num <= total_slots:
                occupied_slots_map[slot_num] = {
                    "sku": it.product.sku,
                    "name": it.product.name,
                }
        current_slot = start_slot + (poles * it.quantity)

    odd_slots = []
    even_slots = []
    for s in range(1, total_slots + 1):
        slot_info = {
            "number": s,
            "occupied": s in occupied_slots_map,
            "sku": occupied_slots_map.get(s, {}).get("sku", ""),
            "name": occupied_slots_map.get(s, {}).get("name", ""),
        }
        if s % 2 != 0:
            odd_slots.append(slot_info)
        else:
            even_slots.append(slot_info)

    # Componentes compatibles con el tablero anfitrión
    compatible_products = []
    if quote.board_product:
        compatible_targets = ProductCompatibility.objects.filter(
            source=quote.board_product,
            relationship_type__in=[
                RelationshipType.COMPATIBLE_WITH,
                RelationshipType.COMPLEMENT_OF,
            ],
        ).values_list("target_id", flat=True)
        compatible_products = list(
            Product.objects.filter(id__in=compatible_targets, is_active=True).order_by(
                "sku"
            )
        )
    if not compatible_products:
        compatible_products = list(
            Product.objects.filter(
                is_active=True, product_type=ProductType.COMPONENT
            ).order_by("sku")
        )

    suggestions = get_quote_suggested_complements(quote)

    context = {
        "quote": quote,
        "items": items,
        "validation": validation,
        "validation_errors_json": json.dumps(validation["errors"]),
        "odd_slots": odd_slots,
        "even_slots": even_slots,
        "compatible_products": compatible_products,
        "suggestions": suggestions,
    }
    return render(request, "quotes/configurator.html", context)


@require_http_methods(["POST"])
def add_quote_item_view(request: HttpRequest, quote_id: int) -> HttpResponse:
    """Controlador web para agregar partidas desde el configurador."""
    quote = get_object_or_404(Quote, id=quote_id)
    product_sku = request.POST.get("product_sku", "").strip()
    quantity = int(request.POST.get("quantity", 1))
    slot_raw = request.POST.get("slot_position", "").strip()
    slot_position = int(slot_raw) if slot_raw.isdigit() else None
    notes = request.POST.get("notes", "").strip()

    try:
        add_item_to_quote(
            quote=quote,
            product_sku=product_sku,
            quantity=quantity,
            slot_position=slot_position,
            notes=notes,
        )
    except (ValidationError, QuoteStateError):
        pass

    return redirect(f"/quotes/{quote.id}/configurator/")


@require_http_methods(["POST"])
def delete_quote_item_view(
    request: HttpRequest, quote_id: int, item_id: int
) -> HttpResponse:
    """Controlador web para eliminar partidas desde el configurador."""
    try:
        remove_quote_item(item_id=item_id)
    except (ValidationError, QuoteStateError):
        pass
    return redirect(f"/quotes/{quote_id}/configurator/")


@require_http_methods(["POST"])
def transition_quote_view(request: HttpRequest, quote_id: int) -> HttpResponse:
    """Controlador web para cambiar el estado de la cotización."""
    target_status = request.POST.get("target_status", "").strip()
    reason = request.POST.get("reason", "").strip()
    try:
        transition_quote_status(
            quote=quote_id, target_status=target_status, reason=reason
        )
    except (ValidationError, QuoteStateError):
        pass
    return redirect(f"/quotes/{quote_id}/bom/")


def bom_detail_view(request: HttpRequest, quote_id: int) -> HttpResponse:
    """Visualización y exportación técnica de la Lista de Materiales (BOM)."""
    quote = get_object_or_404(
        Quote.objects.select_related("board_product"), id=quote_id
    )
    bom = get_quote_bom(quote)
    return render(
        request,
        "quotes/bom_detail.html",
        {
            "quote": quote,
            "bom": bom,
        },
    )
