"""Motor de validación electro-mecánica y verificación de reglas técnicas para CPQ."""

from collections import deque
from typing import Any

from catalog.enums import ProductType, RelationshipType
from catalog.models import Product, ProductCompatibility
from quotes.models import Quote
from quotes.selectors import get_quote_suggested_complements


def validate_quote_configuration(quote: Quote) -> dict[str, Any]:
    """Evalúa las restricciones técnicas de una cotización o ensamble de tablero.

    Reglas verificadas:
    1. Si es ensamble de tablero, existencia y compatibilidad del tablero anfitrión.
    2. Compatibilidad de montaje de derivados (COMPATIBLE_WITH).
    3. Capacidad de espacios físicos (suma de polos vs espacios disponibles).
    4. Límite de corriente máxima de barras vs amperaje de derivados.
    5. Cierre transitivo de dependencias obligatorias (REQUIRES) sin ciclos.
    6. Identificación de complementos recomendados (COMPLEMENT_OF).
    """
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    # Optimización: Cargar partidas con sus productos
    items = list(quote.items.select_related("product").all())
    present_product_ids = {item.product_id for item in items}
    all_present_products = [item.product for item in items]

    total_slots_capacity = 0
    occupied_slots = 0
    available_slots = 0

    if quote.is_board_assembly:
        board = quote.board_product
        if not board:
            errors.append(
                {
                    "code": "MISSING_HOST_BOARD",
                    "message": (
                        "La cotización está marcada como ensamble pero no "
                        "tiene un tablero anfitrión seleccionado."
                    ),
                    "details": {},
                }
            )
        else:
            present_product_ids.add(board.id)
            all_present_products.append(board)

            specs = board.specs or {}
            total_slots_capacity = int(
                specs.get("espacios") or specs.get("slots") or specs.get("polos") or 0
            )
            max_amperage = float(
                specs.get("amperaje_max") or specs.get("amperaje") or 0
            )

            # Pre-cargar compatibilidades directas del tablero
            compatible_targets = set(
                ProductCompatibility.objects.filter(
                    source=board,
                    relationship_type=RelationshipType.COMPATIBLE_WITH,
                ).values_list("target_id", flat=True)
            )

            for item in items:
                prod = item.product
                prod_specs = prod.specs or {}

                # 1. Compatibilidad de derivados (COMPONENT) con el tablero
                if prod.product_type == ProductType.COMPONENT:
                    if prod.id not in compatible_targets:
                        errors.append(
                            {
                                "code": "INCOMPATIBLE_DERIVATIVE",
                                "message": (
                                    f"El producto {prod.sku} ({prod.name}) no es "
                                    f"compatible con el tablero anfitrión {board.sku}."
                                ),
                                "details": {
                                    "product_id": prod.id,
                                    "sku": prod.sku,
                                    "board_sku": board.sku,
                                },
                            }
                        )

                # 2. Conteo de polos / espacios ocupados
                poles = int(prod_specs.get("polos") or prod_specs.get("espacios") or 0)
                if poles > 0:
                    occupied_slots += poles * item.quantity

                # 3. Límite de corriente admisible
                breaker_amp = float(prod_specs.get("amperaje") or 0)
                if max_amperage > 0 and breaker_amp > max_amperage:
                    errors.append(
                        {
                            "code": "AMPERAGE_EXCEEDED",
                            "message": (
                                f"El componente {prod.sku} requiere {breaker_amp}A, "
                                f"excediendo el límite de {max_amperage}A del tablero "
                                f"{board.sku}."
                            ),
                            "details": {
                                "product_id": prod.id,
                                "sku": prod.sku,
                                "breaker_amperage": breaker_amp,
                                "board_amperage": max_amperage,
                            },
                        }
                    )

            # 4. Verificación de capacidad total de espacios
            if total_slots_capacity > 0:
                available_slots = max(0, total_slots_capacity - occupied_slots)
                if occupied_slots > total_slots_capacity:
                    overflow = occupied_slots - total_slots_capacity
                    errors.append(
                        {
                            "code": "INSUFFICIENT_SPACE",
                            "message": (
                                f"Capacidad excedida: se requieren "
                                f"{occupied_slots} espacios pero solo "
                                f"se dispone de {total_slots_capacity}."
                            ),
                            "details": {
                                "overflow": overflow,
                                "required_spaces": occupied_slots,
                                "available_spaces": total_slots_capacity,
                            },
                        }
                    )
            else:
                available_slots = 0

    # 5. Dependencias obligatorias (REQUIRES) con algoritmo de resolución antilazos
    reported_missing_edges: set[tuple[int, int]] = set()

    for origin_product in all_present_products:
        visited_in_path: set[int] = {origin_product.id}
        queue: deque[Product] = deque([origin_product])

        while queue:
            curr = queue.popleft()
            req_edges = ProductCompatibility.objects.filter(
                source=curr,
                relationship_type=RelationshipType.REQUIRES,
            ).select_related("target")

            for edge in req_edges:
                target_prod = edge.target
                if target_prod.id not in present_product_ids:
                    missing_pair = (curr.id, target_prod.id)
                    if missing_pair not in reported_missing_edges:
                        reported_missing_edges.add(missing_pair)
                        errors.append(
                            {
                                "code": "MISSING_REQUIRED_ACCESSORY",
                                "message": (
                                    f"El producto {curr.sku} ({curr.name}) requiere "
                                    f"obligatoriamente el accesorio {target_prod.sku} "
                                    f"({target_prod.name})."
                                ),
                                "details": {
                                    "source_sku": curr.sku,
                                    "source_id": curr.id,
                                    "required_sku": target_prod.sku,
                                    "required_id": target_prod.id,
                                },
                            }
                        )
                else:
                    if target_prod.id not in visited_in_path:
                        visited_in_path.add(target_prod.id)
                        queue.append(target_prod)

    # 6. Sugerencias complementarias no bloqueantes
    suggested_accessories = get_quote_suggested_complements(quote)

    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "total_slots_capacity": total_slots_capacity,
            "occupied_slots": occupied_slots,
            "available_slots": available_slots,
            "total_items": len(items),
        },
        "suggested_accessories": suggested_accessories,
    }
