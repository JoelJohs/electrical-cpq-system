from catalog.enums import ProductType, RelationshipType
from catalog.models import Product, ProductCompatibility


def create_sample_electrical_catalog():
    """Crea una topología de catálogo representativa para pruebas."""
    board, _ = Product.objects.get_or_create(
        sku="TAB-NQ-225",
        defaults={
            "name": "Tablero Alumbrado NQ 225A 30 Polos",
            "slug": "tab-nq-225",
            "product_type": ProductType.BOARD,
            "specs": {"espacios": 30, "amperaje_max": 225, "fases": 3},
            "is_active": True,
        },
    )

    breaker_qo, _ = Product.objects.get_or_create(
        sku="INT-QO-120",
        defaults={
            "name": "Interruptor QO 1P 20A",
            "slug": "int-qo-120",
            "product_type": ProductType.COMPONENT,
            "specs": {
                "polos": 1,
                "amperaje": 20,
                "montaje": "enchufable",
                "ic_ka": 10,
            },
            "is_active": True,
        },
    )

    breaker_edb, _ = Product.objects.get_or_create(
        sku="INT-EDB-3100",
        defaults={
            "name": "Interruptor EDB 3P 100A",
            "slug": "int-edb-3100",
            "product_type": ProductType.COMPONENT,
            "specs": {
                "polos": 3,
                "amperaje": 100,
                "montaje": "atornillable",
                "ic_ka": 18,
            },
            "is_active": True,
        },
    )

    aux_contact, _ = Product.objects.get_or_create(
        sku="ACC-AUX-QO",
        defaults={
            "name": "Contacto Auxiliar para QO",
            "slug": "acc-aux-qo",
            "product_type": ProductType.ACCESSORY,
            "specs": {"tipo_contacto": "1NA/1NC"},
            "is_active": True,
        },
    )

    lug_kit, _ = Product.objects.get_or_create(
        sku="KIT-ZAP-225",
        defaults={
            "name": "Kit Zapata Neutro 225A",
            "slug": "kit-zap-225",
            "product_type": ProductType.ACCESSORY,
            "specs": {"amperaje": 225},
            "is_active": True,
        },
    )

    # Aristas
    ProductCompatibility.objects.get_or_create(
        source=board,
        target=breaker_qo,
        relationship_type=RelationshipType.COMPATIBLE_WITH,
        defaults={"score": 100},
    )

    ProductCompatibility.objects.get_or_create(
        source=board,
        target=lug_kit,
        relationship_type=RelationshipType.COMPLEMENT_OF,
        defaults={"score": 90},
    )

    ProductCompatibility.objects.get_or_create(
        source=breaker_qo,
        target=aux_contact,
        relationship_type=RelationshipType.COMPLEMENT_OF,
        defaults={"score": 100},
    )

    return {
        "board": board,
        "breaker_qo": breaker_qo,
        "breaker_edb": breaker_edb,
        "aux_contact": aux_contact,
        "lug_kit": lug_kit,
    }
