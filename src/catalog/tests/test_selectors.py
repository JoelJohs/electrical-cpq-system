from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility
from catalog.selectors import (
    get_product_by_id,
    get_product_by_nombre_corto,
    get_product_compatibilities,
    get_product_compatibility_tree,
    list_active_products,
)


class CatalogSelectorsTest(TestCase):
    def setUp(self):
        # Crear Tablero Base
        self.tablero = Product.objects.create(
            nombre_corto="NQ-225-30P",
            nombre_largo="Tablero Alumbrado NQ 225A 30 Polos",
            descripcion="Tablero de alumbrado tipo NQ",
            is_active=True,
        )

        # Crear 3 Interruptores compatibles
        self.interruptores = []
        for i in range(1, 4):
            it = Product.objects.create(
                nombre_corto=f"QO-10{i}",
                nombre_largo=f"Interruptor QO {i}P",
                descripcion=f"Interruptor de {i} polo(s)",
                is_active=True,
            )
            self.interruptores.append(it)
            ProductCompatibility.objects.create(
                source=self.tablero,
                target=it,
                relationship_type=RelationshipType.COMPATIBLE_WITH,
                score=100 - i,
            )

        # Crear Accesorio complementario para el Tablero
        self.zapata = Product.objects.create(
            nombre_corto="KIT-ZAP-225",
            nombre_largo="Kit Zapata Neutro",
            descripcion="Zapata de aluminio",
            is_active=True,
        )
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.zapata,
            relationship_type=RelationshipType.COMPLEMENT_OF,
            score=90,
        )

        # Crear Accesorio obligatorio (REQUIRES)
        self.accesorio_req = Product.objects.create(
            nombre_corto="RELE-TERM",
            nombre_largo="Relevador de Sobrecarga",
            descripcion="Accesorio obligatorio de protección",
            is_active=True,
        )
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.accesorio_req,
            relationship_type=RelationshipType.REQUIRES,
            score=100,
        )

    def test_get_product_by_id(self):
        prod = get_product_by_id(self.tablero.id)
        self.assertIsNotNone(prod)
        self.assertEqual(prod.nombre_corto, "NQ-225-30P")

        prod_none = get_product_by_id(999999)
        self.assertIsNone(prod_none)

    def test_get_product_by_nombre_corto(self):
        prod = get_product_by_nombre_corto("NQ-225-30P")
        self.assertIsNotNone(prod)
        self.assertEqual(prod.id, self.tablero.id)

        prod_none = get_product_by_nombre_corto("INEXISTENTE")
        self.assertIsNone(prod_none)

    def test_list_active_products_and_search(self):
        all_prods = list_active_products()
        # 1 tablero + 3 interruptores + 1 zapata + 1 relé = 6
        self.assertEqual(len(all_prods), 6)

        search_res = list_active_products(search="Zapata")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].nombre_corto, "KIT-ZAP-225")

        # Filtrado por categorías para escalas de miles de productos
        tableros = list_active_products(category="tableros")
        self.assertEqual(len(tableros), 1)
        self.assertEqual(tableros[0].nombre_corto, "NQ-225-30P")

        interruptores = list_active_products(category="interruptores")
        self.assertEqual(len(interruptores), 3)

        accesorios = list_active_products(category="accesorios")
        self.assertEqual(len(accesorios), 2)

        # Búsqueda inteligente por tokens / múltiples palabras coincidentes
        multi_search = list_active_products(search="tablero 225")
        self.assertEqual(len(multi_search), 1)
        self.assertEqual(multi_search[0].nombre_corto, "NQ-225-30P")

        multi_qo = list_active_products(search="qo 101")
        self.assertEqual(len(multi_qo), 1)
        self.assertEqual(multi_qo[0].nombre_corto, "QO-101")

    def test_get_product_compatibilities(self):
        compatibilities = get_product_compatibilities(self.tablero.id)
        # 3 comp + 1 zapata + 1 req = 5
        self.assertEqual(len(compatibilities), 5)

        # Filtrado por tipo de relación
        filtered = get_product_compatibilities(
            self.tablero.id,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        self.assertEqual(len(filtered), 3)

    def test_get_product_compatibility_tree(self):
        with CaptureQueriesContext(connection) as ctx:
            tree = get_product_compatibility_tree(self.tablero.id)

        self.assertIsNotNone(tree)
        self.assertEqual(tree["product"]["nombre_corto"], "NQ-225-30P")
        self.assertEqual(len(tree["compatible_components"]), 3)
        self.assertEqual(len(tree["required_accessories"]), 1)
        self.assertEqual(len(tree["complements"]), 1)

        # Máximo 2 consultas SQL
        self.assertLessEqual(len(ctx), 2)

    def test_get_product_compatibility_tree_bidirectional(self):
        # 1. Al consultar el interruptor (hijo),
        # debe retornar el tablero como host_equipment
        it_tree = get_product_compatibility_tree(self.interruptores[0].id)
        self.assertIsNotNone(it_tree)
        self.assertEqual(len(it_tree["host_equipment"]), 1)
        self.assertEqual(it_tree["host_equipment"][0]["nombre_corto"], "NQ-225-30P")

        # 2. Al consultar el accesorio, debe retornar el tablero en used_in_equipment
        zapata_tree = get_product_compatibility_tree(self.zapata.id)
        self.assertIsNotNone(zapata_tree)
        self.assertEqual(len(zapata_tree["used_in_equipment"]), 1)
        self.assertEqual(
            zapata_tree["used_in_equipment"][0]["nombre_corto"], "NQ-225-30P"
        )

    def test_get_product_compatibility_tree_caching_and_invalidation(self):
        """Verifica que el árbol use caché (0 SQL) y se invalide ante cambios."""
        from django.core.cache import cache

        cache.clear()

        # 1. Primera consulta: toca la BD (máximo 2 consultas)
        with CaptureQueriesContext(connection) as ctx1:
            tree1 = get_product_compatibility_tree(self.tablero.id)
        self.assertIsNotNone(tree1)
        self.assertGreater(len(ctx1), 0)
        self.assertLessEqual(len(ctx1), 2)

        # 2. Segunda consulta: debe servirse desde la caché (0 consultas a BD)
        with CaptureQueriesContext(connection) as ctx2:
            tree2 = get_product_compatibility_tree(self.tablero.id)
        self.assertEqual(len(ctx2), 0)
        self.assertEqual(tree1, tree2)

        # 3. Modificación del producto: dispara señal post_save e incrementa versión
        self.tablero.nombre_largo = "Tablero NQ 225A Actualizado"
        self.tablero.save()

        # 4. Tercera consulta: al invalidarse, vuelve a consultar la BD
        with CaptureQueriesContext(connection) as ctx3:
            tree3 = get_product_compatibility_tree(self.tablero.id)
        self.assertGreater(len(ctx3), 0)
        self.assertEqual(
            tree3["product"]["nombre_largo"], "Tablero NQ 225A Actualizado"
        )
