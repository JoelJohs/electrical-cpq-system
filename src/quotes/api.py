"""API REST tipada con Django Ninja para gestión de cotizaciones técnicas y CPQ."""

from typing import Any, Optional

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router

from catalog.api import api
from quotes.models import Quote
from quotes.rules import validate_quote_configuration
from quotes.schemas import (
    AddQuoteItemSchema,
    BOMResponseSchema,
    CreateQuoteSchema,
    QuoteDetailSchema,
    TransitionStatusSchema,
    UpdateQuoteItemSchema,
    ValidationResultSchema,
)
from quotes.selectors import get_quote_bom, list_quotes
from quotes.services import (
    QuoteStateError,
    add_item_to_quote,
    create_quote,
    remove_quote_item,
    transition_quote_status,
    update_quote_item,
)

quotes_router = Router(tags=["Cotizaciones y CPQ"])


def format_quote_detail(quote: Quote) -> dict[str, Any]:
    """Serializa una cotización técnica completa con sus partidas."""
    items = list(quote.items.select_related("product").order_by("slot_position", "id"))
    return {
        "id": quote.id,
        "folio": quote.folio,
        "client_name": quote.client_name,
        "project_reference": quote.project_reference,
        "status": quote.status,
        "is_board_assembly": quote.is_board_assembly,
        "board_sku": quote.board_product.sku if quote.board_product else None,
        "board_name": quote.board_product.name if quote.board_product else None,
        "items_count": len(items),
        "notes": quote.notes,
        "created_at": quote.created_at,
        "items": [
            {
                "id": it.id,
                "product_sku": it.product.sku,
                "product_name": it.product.name,
                "product_type": it.product.product_type,
                "quantity": it.quantity,
                "slot_position": it.slot_position,
                "notes": it.notes,
                "specs": it.product.specs or {},
            }
            for it in items
        ],
    }


@quotes_router.get("/", response=list[QuoteDetailSchema])
def list_quotes_endpoint(
    request,
    status: Optional[str] = None,
    client_name: Optional[str] = None,
):
    """Lista cotizaciones registradas con filtros opcionales de estado o cliente."""
    quotes = list_quotes(status=status, client_name=client_name)
    return [format_quote_detail(q) for q in quotes]


@quotes_router.post("/", response={201: QuoteDetailSchema, 400: dict})
def create_quote_endpoint(request, payload: CreateQuoteSchema):
    """Crea una nueva cotización técnica o ensamble de tablero en estado DRAFT."""
    try:
        quote = create_quote(
            client_name=payload.client_name,
            project_reference=payload.project_reference,
            is_board_assembly=payload.is_board_assembly,
            board_sku=payload.board_sku,
            notes=payload.notes,
        )
        return 201, format_quote_detail(quote)
    except ValidationError as exc:
        msg = exc.message_dict if hasattr(exc, "message_dict") else str(exc)
        return 400, {"detail": msg}


@quotes_router.get("/{int:quote_id}/", response=QuoteDetailSchema)
def get_quote_endpoint(request, quote_id: int):
    """Obtiene el detalle completo de una cotización y sus partidas."""
    quote = get_object_or_404(
        Quote.objects.select_related("board_product"), id=quote_id
    )
    return format_quote_detail(quote)


@quotes_router.post(
    "/{int:quote_id}/items/",
    response={201: QuoteDetailSchema, 400: dict, 409: dict},
)
def add_item_endpoint(request, quote_id: int, payload: AddQuoteItemSchema):
    """Agrega un producto/partida a la cotización."""
    quote = get_object_or_404(Quote, id=quote_id)
    try:
        add_item_to_quote(
            quote=quote,
            product_sku=payload.product_sku,
            quantity=payload.quantity,
            slot_position=payload.slot_position,
            notes=payload.notes,
        )
        quote.refresh_from_db()
        return 201, format_quote_detail(quote)
    except QuoteStateError as exc:
        return 409, {"detail": str(exc)}
    except ValidationError as exc:
        msg = exc.message_dict if hasattr(exc, "message_dict") else str(exc)
        return 400, {"detail": msg}


@quotes_router.patch(
    "/{int:quote_id}/items/{int:item_id}/",
    response={200: QuoteDetailSchema, 400: dict, 409: dict},
)
def update_item_endpoint(
    request, quote_id: int, item_id: int, payload: UpdateQuoteItemSchema
):
    """Actualiza cantidad o ranura de una partida existente."""
    quote = get_object_or_404(Quote, id=quote_id)
    try:
        update_quote_item(
            item_id=item_id,
            quantity=payload.quantity,
            slot_position=payload.slot_position,
            notes=payload.notes,
        )
        quote.refresh_from_db()
        return 200, format_quote_detail(quote)
    except QuoteStateError as exc:
        return 409, {"detail": str(exc)}
    except ValidationError as exc:
        msg = exc.message_dict if hasattr(exc, "message_dict") else str(exc)
        return 400, {"detail": msg}


@quotes_router.delete(
    "/{int:quote_id}/items/{int:item_id}/",
    response={200: QuoteDetailSchema, 400: dict, 409: dict},
)
def delete_item_endpoint(request, quote_id: int, item_id: int):
    """Elimina una partida de la cotización."""
    quote = get_object_or_404(Quote, id=quote_id)
    try:
        remove_quote_item(item_id=item_id)
        quote.refresh_from_db()
        return 200, format_quote_detail(quote)
    except QuoteStateError as exc:
        return 409, {"detail": str(exc)}
    except ValidationError as exc:
        msg = exc.message_dict if hasattr(exc, "message_dict") else str(exc)
        return 400, {"detail": msg}


@quotes_router.post("/{int:quote_id}/validate/", response=ValidationResultSchema)
def validate_quote_endpoint(request, quote_id: int):
    """Evalúa las reglas técnicas y restricciones de tablero sobre la cotización."""
    quote = get_object_or_404(
        Quote.objects.select_related("board_product"), id=quote_id
    )
    return validate_quote_configuration(quote)


@quotes_router.get("/{int:quote_id}/bom/", response=BOMResponseSchema)
def get_quote_bom_endpoint(request, quote_id: int):
    """Genera la Lista de Materiales (BOM) consolidada del ensamble o cotización."""
    quote = get_object_or_404(
        Quote.objects.select_related("board_product"), id=quote_id
    )
    return get_quote_bom(quote)


@quotes_router.post(
    "/{int:quote_id}/transition/",
    response={200: QuoteDetailSchema, 400: dict, 409: dict},
)
def transition_quote_status_endpoint(
    request, quote_id: int, payload: TransitionStatusSchema
):
    """Transiciona el estado del ciclo de vida de la cotización."""
    try:
        quote = transition_quote_status(
            quote=quote_id,
            target_status=payload.target_status,
            reason=payload.reason or "",
        )
        return 200, format_quote_detail(quote)
    except QuoteStateError as exc:
        return 409, {"detail": str(exc)}
    except ValidationError as exc:
        msg = exc.message_dict if hasattr(exc, "message_dict") else str(exc)
        return 400, {"detail": msg}


# Registrar router en la API Ninja global
api.add_router("/v1/quotes", quotes_router)
