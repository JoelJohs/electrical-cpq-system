from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.db.models import Q

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility


def get_product_by_sku(sku: str) -> Optional[Product]:
    """Retorna un producto activo por su SKU o None si no existe."""
    return Product.objects.filter(sku=sku, is_active=True).first()


def get_product_compatibilities(
    sku: str,
    relationship_type: Optional[str] = None,
) -> List[ProductCompatibility]:
    """
    Retorna las aristas de compatibilidad directas donde el producto es 'source'.
    Utiliza select_related('target') para evitar consultas N+1 sobre los
    productos destino.
    """
    product = get_product_by_sku(sku)
    if not product:
        return []

    queryset = (
        ProductCompatibility.objects.filter(
            source=product,
            target__is_active=True,
        )
        .select_related("target")
        .order_by("-score", "target__name")
    )

    if relationship_type:
        queryset = queryset.filter(relationship_type=relationship_type)

    return list(queryset)


def get_product_compatibility_tree(sku: str) -> Optional[Dict[str, Any]]:
    """
    Resuelve el árbol jerárquico completo para un producto contenedor (ej. Tablero)
    en exactamente 2 consultas SQL fijas:
      1. Obtener el producto anfitrión.
      2. Obtener todas las aristas directas del anfitrión y los accesorios de los
         componentes mediante una única consulta SQL combinada con subconsulta y
         select_related('target').
    """
    product = get_product_by_sku(sku)
    if not product:
        return None

    # Subconsulta para identificar los IDs de componentes compatibles con el anfitrión
    compatible_components_subquery = ProductCompatibility.objects.filter(
        source_id=product.id,
        relationship_type=RelationshipType.COMPATIBLE_WITH,
    ).values("target_id")

    # Consulta 2: Todas las aristas del anfitrión + accesorios en 1 solo query SQL
    all_edges = (
        ProductCompatibility.objects.filter(
            Q(source_id=product.id)
            | Q(
                source_id__in=compatible_components_subquery,
                relationship_type=RelationshipType.COMPLEMENT_OF,
            ),
            target__is_active=True,
        )
        .select_related("target")
        .order_by("-score")
    )

    # Clasificar en memoria sin tocar la base de datos
    direct_components = []
    direct_accessories = []
    accessories_by_component = defaultdict(list)

    for edge in all_edges:
        if edge.source_id == product.id:
            if edge.relationship_type == RelationshipType.COMPATIBLE_WITH:
                direct_components.append(edge)
            elif edge.relationship_type == RelationshipType.COMPLEMENT_OF:
                direct_accessories.append(
                    {
                        "id": edge.target.id,
                        "sku": edge.target.sku,
                        "name": edge.target.name,
                        "product_type": edge.target.product_type,
                        "relationship_type": edge.relationship_type,
                        "score": edge.score,
                        "notes": edge.notes,
                        "specs": edge.target.specs,
                    }
                )
        else:
            # Es un accesorio de un componente derivado
            accessories_by_component[edge.source_id].append(
                {
                    "id": edge.target.id,
                    "sku": edge.target.sku,
                    "name": edge.target.name,
                    "product_type": edge.target.product_type,
                    "relationship_type": edge.relationship_type,
                    "score": edge.score,
                    "notes": edge.notes,
                    "specs": edge.target.specs,
                }
            )

    # Estructurar componentes con sus respectivos accesorios anidados
    formatted_components = []
    for comp_edge in direct_components:
        comp_target = comp_edge.target
        formatted_components.append(
            {
                "id": comp_target.id,
                "sku": comp_target.sku,
                "name": comp_target.name,
                "product_type": comp_target.product_type,
                "relationship_type": comp_edge.relationship_type,
                "score": comp_edge.score,
                "notes": comp_edge.notes,
                "specs": comp_target.specs,
                "accessories": accessories_by_component.get(comp_target.id, []),
            }
        )

    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "product_type": product.product_type,
        "specs": product.specs,
        "compatible_components": formatted_components,
        "direct_accessories": direct_accessories,
    }
