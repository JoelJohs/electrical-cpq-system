from typing import Any, Dict, List, Optional

from django.db.models import QuerySet

from catalog.enums import RelationshipType
from catalog.models import ProductCompatibility
from quotes.models import Quote, QuoteItem


def get_quote_by_id(quote_id: int) -> Optional[Quote]:
    """Obtiene una cotización por su ID junto con el producto de tablero anfitrión."""
    return (
        Quote.objects.select_related("board_product", "created_by")
        .filter(id=quote_id)
        .first()
    )


def get_quote_by_folio(folio: str) -> Optional[Quote]:
    """Obtiene una cotización por su folio único."""
    return (
        Quote.objects.select_related("board_product", "created_by")
        .filter(folio=folio.strip())
        .first()
    )


def list_quotes(
    status: Optional[str] = None,
    client_name: Optional[str] = None,
) -> QuerySet[Quote]:
    """Lista cotizaciones con filtros opcionales."""
    queryset = Quote.objects.select_related("board_product").all()
    if status:
        queryset = queryset.filter(status=status)
    if client_name:
        queryset = queryset.filter(client_name__icontains=client_name.strip())
    return queryset


def get_quote_items(quote: Quote) -> List[QuoteItem]:
    """Retorna las partidas de una cotización con sus productos precargados."""
    return list(
        QuoteItem.objects.filter(quote=quote)
        .select_related("product")
        .order_by("slot_position", "id")
    )


def get_quote_suggested_complements(quote: Quote) -> List[Dict[str, Any]]:
    """
    Retorna sugerencias de accesorios complementarios (COMPLEMENT_OF)
    para los productos presentes en la cotización que aún no hayan sido agregados.
    """
    items = get_quote_items(quote)
    product_ids_in_quote = {item.product_id for item in items}
    if quote.is_board_assembly and quote.board_product_id:
        product_ids_in_quote.add(quote.board_product_id)

    if not product_ids_in_quote:
        return []

    # Buscar aristas COMPLEMENT_OF salientes desde los productos en cotización
    edges = (
        ProductCompatibility.objects.filter(
            source_id__in=product_ids_in_quote,
            relationship_type=RelationshipType.COMPLEMENT_OF,
            target__is_active=True,
        )
        .select_related("source", "target")
        .order_by("-score", "target__name")
    )

    suggestions = []
    seen_target_ids = set()
    for edge in edges:
        # Excluir productos que ya están en la cotización
        if edge.target_id in product_ids_in_quote or edge.target_id in seen_target_ids:
            continue
        seen_target_ids.add(edge.target_id)
        suggestions.append(
            {
                "sku": edge.target.sku,
                "name": edge.target.name,
                "product_type": edge.target.product_type,
                "relationship_type": edge.relationship_type,
                "source_sku": edge.source.sku,
                "score": edge.score,
                "notes": edge.notes,
                "specs": edge.target.specs,
            }
        )

    return suggestions


def get_quote_bom(quote: Quote) -> Dict[str, Any]:
    """Genera la Lista de Materiales (BOM - Bill of Materials) técnica y determinista.

    Consolida:
    - Tablero anfitrión (si aplica) con cantidad 1.
    - Partidas individuales con posiciones de ranura y notas.
    - Agregación consolidada de materiales por SKU sumando cantidades.
    - Conteo total de piezas físicas requeridas para ensamble/surtido.
    """
    items = get_quote_items(quote)
    aggregated_map: Dict[str, Dict[str, Any]] = {}
    total_components_count = 0

    board_info = None
    if quote.is_board_assembly and quote.board_product:
        board = quote.board_product
        board_info = {
            "sku": board.sku,
            "name": board.name,
            "product_type": board.product_type,
            "specs": board.specs,
            "quantity": 1,
        }
        aggregated_map[board.sku] = {
            "sku": board.sku,
            "name": board.name,
            "product_type": board.product_type,
            "total_quantity": 1,
        }
        total_components_count += 1

    detailed_items = []
    for item in items:
        prod = item.product
        detailed_items.append(
            {
                "item_id": item.id,
                "sku": prod.sku,
                "name": prod.name,
                "product_type": prod.product_type,
                "quantity": item.quantity,
                "slot_position": item.slot_position,
                "notes": item.notes,
                "specs": prod.specs,
            }
        )

        if prod.sku in aggregated_map:
            aggregated_map[prod.sku]["total_quantity"] += item.quantity
        else:
            aggregated_map[prod.sku] = {
                "sku": prod.sku,
                "name": prod.name,
                "product_type": prod.product_type,
                "total_quantity": item.quantity,
            }
        total_components_count += item.quantity

    aggregated_materials = sorted(aggregated_map.values(), key=lambda m: m["sku"])

    return {
        "folio": quote.folio,
        "client_name": quote.client_name,
        "project_reference": quote.project_reference,
        "is_board_assembly": quote.is_board_assembly,
        "status": quote.status,
        "board": board_info,
        "items": detailed_items,
        "aggregated_materials": aggregated_materials,
        "total_components_count": total_components_count,
        "created_at": quote.created_at.isoformat() if quote.created_at else None,
    }
