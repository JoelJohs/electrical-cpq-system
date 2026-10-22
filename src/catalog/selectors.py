"""Consultas y selectores optimizados para catálogo y grafo de compatibilidades."""

from typing import Any, Optional

from django.core.cache import cache
from django.db.models import Case, IntegerField, Q, QuerySet, Value, When

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility


def get_product_by_id(product_id: int) -> Optional[Product]:
    """Retorna un producto activo por su ID numérico."""
    return Product.objects.filter(id=product_id, is_active=True).first()


def get_product_by_nombre_corto(nombre_corto: str) -> Optional[Product]:
    """Retorna un producto activo por su nombre corto."""
    return Product.objects.filter(
        nombre_corto__iexact=nombre_corto.strip(), is_active=True
    ).first()


def list_active_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
) -> QuerySet[Product]:
    """Lista productos activos con búsqueda inteligente y filtro por categoría."""
    qs = Product.objects.filter(is_active=True)

    if category:
        cat = category.strip().lower()
        tablero_q = (
            Q(nombre_largo__icontains="tablero")
            | Q(nombre_largo__icontains="panel")
            | Q(nombre_largo__icontains="gabinete")
            | Q(nombre_corto__istartswith="NQ")
            | Q(nombre_corto__istartswith="NF")
            | Q(nombre_corto__istartswith="I-LINE")
        )
        interruptor_q = (
            Q(nombre_largo__icontains="interruptor")
            | Q(nombre_largo__icontains="breaker")
            | Q(nombre_corto__istartswith="QO")
            | Q(nombre_corto__istartswith="EDB")
            | Q(nombre_corto__istartswith="FA")
            | Q(nombre_corto__istartswith="LA")
            | Q(nombre_corto__istartswith="HOM")
        )
        if cat == "tableros":
            qs = qs.filter(tablero_q)
        elif cat == "interruptores":
            qs = qs.filter(interruptor_q)
        elif cat == "accesorios":
            qs = qs.exclude(tablero_q | interruptor_q)

    if search:
        query = search.strip()
        tokens = [t for t in query.split() if t]
        for token in tokens:
            token_clean = token.replace("-", "")
            token_q = (
                Q(nombre_corto__icontains=token)
                | Q(nombre_largo__icontains=token)
                | Q(descripcion__icontains=token)
            )
            if token_clean:
                token_q |= Q(nombre_corto__icontains=token_clean)
            qs = qs.filter(token_q)

        # Ranking de relevancia SQL determinista (exacto > prefijo > parcial)
        qs = qs.annotate(
            search_rank=Case(
                When(nombre_corto__iexact=query, then=Value(100)),
                When(nombre_corto__istartswith=query, then=Value(80)),
                When(nombre_corto__icontains=query, then=Value(60)),
                When(nombre_largo__icontains=query, then=Value(40)),
                default=Value(10),
                output_field=IntegerField(),
            )
        ).order_by("-search_rank", "nombre_corto")
    else:
        qs = qs.order_by("nombre_corto")

    return qs


def get_product_compatibilities(
    product_id: int,
    relationship_type: Optional[str] = None,
) -> list[ProductCompatibility]:
    """Retorna las aristas de compatibilidad directas de un producto."""
    product = get_product_by_id(product_id)
    if not product:
        return []

    queryset = (
        ProductCompatibility.objects.filter(
            source=product,
            target__is_active=True,
        )
        .select_related("target")
        .order_by("-score", "target__nombre_corto")
    )

    if relationship_type:
        queryset = queryset.filter(relationship_type=relationship_type)

    return list(queryset)


def get_product_compatibility_tree(
    product_id: int,
    use_cache: bool = True,
) -> Optional[dict[str, Any]]:
    """Resuelve el grafo bidireccional del producto con soporte de caché.

    Obtiene componentes compatibles, accesorios obligatorios, complementos sugeridos,
    alternativas directas, y relaciones entrantes (equipos anfitriones donde se monta
    y equipos que requieren o complementan con este producto).
    """
    version = cache.get("catalog:cache_version", 1)
    cache_key = f"catalog:v{version}:tree:{product_id}"

    if use_cache:
        cached_tree = cache.get(cache_key)
        if cached_tree is not None:
            return cached_tree

    product = get_product_by_id(product_id)
    if not product:
        return None

    edges = (
        ProductCompatibility.objects.filter(
            Q(source=product, target__is_active=True)
            | Q(target=product, source__is_active=True)
        )
        .select_related("source", "target")
        .order_by("-score", "target__nombre_corto")
    )

    compatible_components = []
    required_accessories = []
    complements = []
    alternatives = []
    host_equipment = []
    used_in_equipment = []
    alternative_for = []

    for edge in edges:
        # 1. Relación saliente: este producto apunta hacia otro producto
        if edge.source_id == product.id:
            t = edge.target
            target_dict = {
                "id": t.id,
                "nombre_corto": t.nombre_corto,
                "nombre_largo": t.nombre_largo,
                "descripcion": t.descripcion,
                "is_active": t.is_active,
                "category": t.category,
                "notes": edge.notes,
            }
            if edge.relationship_type == RelationshipType.COMPATIBLE_WITH:
                compatible_components.append(target_dict)
            elif edge.relationship_type == RelationshipType.REQUIRES:
                required_accessories.append(target_dict)
            elif edge.relationship_type == RelationshipType.COMPLEMENT_OF:
                complements.append(target_dict)
            elif edge.relationship_type == RelationshipType.ALTERNATIVE_TO:
                alternatives.append(target_dict)

        # 2. Relación entrante: otro producto apunta hacia este producto
        if edge.target_id == product.id:
            s = edge.source
            source_dict = {
                "id": s.id,
                "nombre_corto": s.nombre_corto,
                "nombre_largo": s.nombre_largo,
                "descripcion": s.descripcion,
                "is_active": s.is_active,
                "category": s.category,
                "notes": edge.notes,
            }
            if edge.relationship_type == RelationshipType.COMPATIBLE_WITH:
                host_equipment.append(source_dict)
            elif edge.relationship_type in (
                RelationshipType.REQUIRES,
                RelationshipType.COMPLEMENT_OF,
            ):
                used_in_equipment.append(source_dict)
            elif edge.relationship_type == RelationshipType.ALTERNATIVE_TO:
                alternative_for.append(source_dict)

    result = {
        "product": {
            "id": product.id,
            "nombre_corto": product.nombre_corto,
            "nombre_largo": product.nombre_largo,
            "descripcion": product.descripcion,
            "is_active": product.is_active,
            "category": product.category,
        },
        "compatible_components": compatible_components,
        "required_accessories": required_accessories,
        "complements": complements,
        "alternatives": alternatives,
        "host_equipment": host_equipment,
        "used_in_equipment": used_in_equipment,
        "alternative_for": alternative_for,
    }
    if use_cache:
        cache.set(cache_key, result, timeout=1800)
    return result
