"""Servicios transaccionales para cotizaciones y ensambles de tableros."""

from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.enums import ProductType
from catalog.selectors import get_product_by_sku
from quotes.enums import QuoteStatus
from quotes.models import Quote, QuoteItem


class QuoteStateError(Exception):
    """Excepción al intentar modificar una cotización en estado inmutable."""

    pass


@transaction.atomic
def create_quote(
    client_name: str,
    project_reference: str = "",
    is_board_assembly: bool = False,
    board_sku: str | None = None,
    notes: str = "",
) -> Quote:
    """Crea una nueva cotización técnica en estado DRAFT."""
    board_product = None
    if is_board_assembly:
        if not board_sku:
            raise ValidationError(
                {"board_sku": "Debe especificar un SKU para ensamble de tablero."}
            )
        board_product = get_product_by_sku(board_sku)
        if not board_product:
            raise ValidationError(
                {"board_sku": f"Tablero con SKU '{board_sku}' no encontrado."}
            )
        if board_product.product_type != ProductType.BOARD:
            raise ValidationError(
                {"board_sku": f"El producto '{board_sku}' no es un tablero (BOARD)."}
            )

    quote = Quote(
        client_name=client_name.strip(),
        project_reference=project_reference.strip(),
        is_board_assembly=is_board_assembly,
        board_product=board_product,
        notes=notes.strip(),
        status=QuoteStatus.DRAFT,
    )
    quote.clean()
    quote.save()
    return quote


@transaction.atomic
def add_item_to_quote(
    quote: Quote | int | None = None,
    product_sku: str = "",
    quantity: int = 1,
    slot_position: int | None = None,
    notes: str = "",
    quote_id: int | None = None,
) -> QuoteItem:
    """Agrega una partida de producto a una cotización editable."""
    if isinstance(quote, Quote):
        quote_obj = quote
    else:
        target_id = quote if isinstance(quote, int) else quote_id
        if not target_id:
            raise ValidationError({"quote_id": "Debe especificar una cotización."})
        quote_obj = Quote.objects.select_for_update().filter(id=target_id).first()

    if not quote_obj:
        raise ValidationError(
            {"quote_id": f"Cotización con ID {target_id} no encontrada."}
        )

    if not quote_obj.can_edit():
        raise QuoteStateError(
            f"La cotización {quote_obj.folio} está en estado "
            f"'{quote_obj.get_status_display()}' y no admite modificaciones."
        )

    product = get_product_by_sku(product_sku)
    if not product:
        raise ValidationError(
            {"product_sku": f"Producto con SKU '{product_sku}' no encontrado."}
        )
    if not product.is_active:
        raise ValidationError(
            {"product_sku": f"El producto '{product_sku}' está inactivo."}
        )

    if quantity < 1:
        raise ValidationError({"quantity": "La cantidad debe ser mayor o igual a 1."})

    existing_item = QuoteItem.objects.filter(
        quote=quote_obj,
        product=product,
        slot_position=slot_position,
    ).first()

    if existing_item:
        existing_item.quantity += quantity
        if notes:
            existing_item.notes = notes
        existing_item.full_clean()
        existing_item.save()
        item = existing_item
    else:
        item = QuoteItem(
            quote=quote_obj,
            product=product,
            quantity=quantity,
            slot_position=slot_position,
            notes=notes.strip(),
        )
        item.full_clean()
        item.save()

    if quote_obj.status == QuoteStatus.VALIDATED:
        quote_obj.status = QuoteStatus.DRAFT
        quote_obj.save(update_fields=["status", "updated_at"])

    return item


@transaction.atomic
def update_quote_item(
    item_id: int,
    quantity: int | None = None,
    slot_position: int | None = None,
    notes: str | None = None,
) -> QuoteItem:
    """Actualiza una partida de cotización existente."""
    item = QuoteItem.objects.select_related("quote").filter(id=item_id).first()
    if not item:
        raise ValidationError({"item_id": f"Partida con ID {item_id} no encontrada."})

    quote = item.quote
    if not quote.can_edit():
        raise QuoteStateError(
            f"La cotización {quote.folio} está en estado "
            f"'{quote.get_status_display()}' y no admite modificaciones."
        )

    if quantity is not None:
        if quantity < 1:
            raise ValidationError(
                {"quantity": "La cantidad debe ser mayor o igual a 1."}
            )
        item.quantity = quantity

    if slot_position is not None:
        item.slot_position = slot_position

    if notes is not None:
        item.notes = notes.strip()

    item.full_clean()
    item.save()

    if quote.status == QuoteStatus.VALIDATED:
        quote.status = QuoteStatus.DRAFT
        quote.save(update_fields=["status", "updated_at"])

    return item


@transaction.atomic
def remove_quote_item(item_id: int) -> int:
    """Elimina una partida de cotización y retorna el quote_id afectado."""
    item = QuoteItem.objects.select_related("quote").filter(id=item_id).first()
    if not item:
        raise ValidationError({"item_id": f"Partida con ID {item_id} no encontrada."})

    quote = item.quote
    if not quote.can_edit():
        raise QuoteStateError(
            f"La cotización {quote.folio} está en estado "
            f"'{quote.get_status_display()}' y no admite modificaciones."
        )

    quote_id = quote.id
    item.delete()

    if quote.status == QuoteStatus.VALIDATED:
        quote.status = QuoteStatus.DRAFT
        quote.save(update_fields=["status", "updated_at"])

    return quote_id


VALID_TRANSITIONS: dict[str, list[str]] = {
    QuoteStatus.DRAFT: [QuoteStatus.VALIDATED, QuoteStatus.CANCELLED],
    QuoteStatus.VALIDATED: [QuoteStatus.SENT, QuoteStatus.DRAFT, QuoteStatus.CANCELLED],
    QuoteStatus.SENT: [QuoteStatus.ACCEPTED, QuoteStatus.CANCELLED],
    QuoteStatus.ACCEPTED: [],
    QuoteStatus.CANCELLED: [],
}


@transaction.atomic
def transition_quote_status(
    quote: Quote | int,
    target_status: str,
    reason: str = "",
) -> Quote:
    """Ejecuta una transición de estado en la máquina de estados de Quote."""
    from quotes.rules import validate_quote_configuration

    if isinstance(quote, Quote):
        quote_obj = Quote.objects.select_for_update().filter(id=quote.id).first()
    else:
        quote_obj = Quote.objects.select_for_update().filter(id=quote).first()

    if not quote_obj:
        raise ValidationError({"quote_id": "Cotización no encontrada."})

    allowed = VALID_TRANSITIONS.get(quote_obj.status, [])
    if target_status not in allowed:
        raise QuoteStateError(
            f"Transición no permitida desde '{quote_obj.status}' "
            f"hacia '{target_status}'."
        )

    if target_status == QuoteStatus.VALIDATED:
        if not quote_obj.items.exists():
            raise ValidationError(
                {"items": "No se puede validar una cotización sin partidas."}
            )
        val_result = validate_quote_configuration(quote_obj)
        if not val_result["valid"]:
            raise ValidationError(
                {
                    "validation": (
                        "La cotización presenta conflictos electro-mecánicos "
                        "y no puede validarse."
                    ),
                    "errors": val_result["errors"],
                }
            )

    quote_obj.status = target_status
    if reason:
        prefix = f"\n[Cambio de estado a {target_status}]: {reason.strip()}"
        quote_obj.notes = f"{quote_obj.notes}{prefix}".strip()

    quote_obj.full_clean()
    quote_obj.save(update_fields=["status", "notes", "updated_at"])
    return quote_obj
