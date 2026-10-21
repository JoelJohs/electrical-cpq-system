from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from catalog.enums import ProductType, RelationshipType
from catalog.models import Product, ProductCompatibility
from catalog.selectors import (
    get_product_by_sku,
    get_product_compatibilities,
    get_product_compatibility_tree,
)


class CatalogSelectorsTest(TestCase):
    def setUp(self):
        # Crear Tablero
        self.tablero = Product.objects.create(
            sku="TAB-NQ-225",
            name="Tablero Alumbrado NQ 225A 30 Polos",
            slug="tab-nq-225",
            product_type=ProductType.BOARD,
            specs={"espacios": 30, "amperaje_max": 225},
            is_active=True,
        )

        # Crear 3 Interruptores compatibles
        self.interruptores = []
        for i in range(1, 4):
            it = Product.objects.create(
                sku=f"INT-QO-10{i}",
                name=f"Interruptor QO {i}P",
                slug=f"int-qo-10{i}",
                product_type=ProductType.COMPONENT,
                specs={"polos": i},
                is_active=True,
            )
            self.interruptores.append(it)
            ProductCompatibility.objects.create(
                source=self.tablero,
                target=it,
                relationship_type=RelationshipType.COMPATIBLE_WITH,
                score=100 - i,
            )

        # Crear Accesorio directo para el Tablero
        self.zapata = Product.objects.create(
            sku="KIT-ZAP-225",
            name="Kit Zapata Neutro",
            slug="kit-zap-225",
            product_type=ProductType.ACCESSORY,
            specs={"calibre": "4-300"},
            is_active=True,
        )
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.zapata,
            relationship_type=RelationshipType.COMPLEMENT_OF,
            score=90,
        )

        # Crear Accesorios para los Interruptores
        for it in self.interruptores:
            acc = Product.objects.create(
                sku=f"ACC-AUX-{it.sku}",
                name=f"Auxiliar para {it.sku}",
                slug=f"acc-aux-{it.slug}",
                product_type=ProductType.ACCESSORY,
                specs={},
                is_active=True,
            )
            ProductCompatibility.objects.create(
                source=it,
                target=acc,
                relationship_type=RelationshipType.COMPLEMENT_OF,
                score=100,
            )

    def test_get_product_by_sku(self):
        prod = get_product_by_sku("TAB-NQ-225")
        self.assertIsNotNone(prod)
        self.assertEqual(prod.sku, "TAB-NQ-225")

        prod_none = get_product_by_sku("NON-EXISTENT")
        self.assertIsNone(prod_none)

    def test_get_product_compatibilities(self):
        compatibilities = get_product_compatibilities("TAB-NQ-225")
        # 3 interruptores + 1 zapata = 4
        self.assertEqual(len(compatibilities), 4)

        # Filtrado por tipo de relación
        filtered = get_product_compatibilities(
            "TAB-NQ-225",
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        self.assertEqual(len(filtered), 3)

    def test_get_product_compatibility_tree_queries_count(self):
        # Prueba crítica de rendimiento: resolución en <= 2 consultas SQL fijas
        with CaptureQueriesContext(connection) as ctx:
            tree = get_product_compatibility_tree("TAB-NQ-225")

        self.assertIsNotNone(tree)
        self.assertEqual(tree["sku"], "TAB-NQ-225")
        self.assertEqual(len(tree["compatible_components"]), 3)
        self.assertEqual(len(tree["direct_accessories"]), 1)

        # Verificar que cada componente tenga su accesorio
        for comp in tree["compatible_components"]:
            self.assertEqual(len(comp["accessories"]), 1)

        # Máximo 2 consultas SQL (1 para el producto y compatibilidades directas,
        # 1 para accesorios de componentes)
        self.assertLessEqual(
            len(ctx),
            2,
            f"Se esperaban <= 2 consultas SQL, pero se ejecutaron {len(ctx)}",
        )
