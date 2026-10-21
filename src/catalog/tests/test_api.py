from django.test import Client, TestCase

from catalog.enums import ProductType, RelationshipType
from catalog.models import Product, ProductCompatibility


class CatalogAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tablero = Product.objects.create(
            sku="TAB-NQ-225",
            name="Tablero Alumbrado NQ 225A 30 Polos",
            slug="tab-nq-225",
            product_type=ProductType.BOARD,
            specs={"espacios": 30, "amperaje_max": 225},
            is_active=True,
        )
        self.interruptor = Product.objects.create(
            sku="INT-QO-120",
            name="Interruptor QO 1P 20A",
            slug="int-qo-120",
            product_type=ProductType.COMPONENT,
            specs={"polos": 1},
            is_active=True,
        )
        self.accesorio = Product.objects.create(
            sku="ACC-AUX-QO",
            name="Contacto Auxiliar 1NA/1NC",
            slug="acc-aux-qo",
            product_type=ProductType.ACCESSORY,
            specs={},
            is_active=True,
        )

        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.interruptor,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
            score=100,
            notes="Hasta 30 circuitos",
        )
        ProductCompatibility.objects.create(
            source=self.interruptor,
            target=self.accesorio,
            relationship_type=RelationshipType.COMPLEMENT_OF,
            score=95,
        )

    def test_list_products_endpoint(self):
        response = self.client.get("/api/v1/catalog/products/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("items", data)
        self.assertEqual(data["count"], 3)

    def test_filter_products_by_type(self):
        response = self.client.get("/api/v1/catalog/products/?product_type=BOARD")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["items"][0]["sku"], "TAB-NQ-225")

    def test_get_product_detail(self):
        response = self.client.get("/api/v1/catalog/products/TAB-NQ-225/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["sku"], "TAB-NQ-225")
        self.assertEqual(data["product_type"], "BOARD")

    def test_get_product_detail_404(self):
        response = self.client.get("/api/v1/catalog/products/NOT-FOUND/")
        self.assertEqual(response.status_code, 404)

    def test_get_product_compatibilities(self):
        response = self.client.get(
            "/api/v1/catalog/products/TAB-NQ-225/compatibilities/"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["product"]["sku"], "TAB-NQ-225")
        self.assertEqual(len(data["compatibilities"]), 1)
        self.assertEqual(data["compatibilities"][0]["target_sku"], "INT-QO-120")

    def test_get_product_tree(self):
        response = self.client.get("/api/v1/catalog/products/TAB-NQ-225/tree/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["sku"], "TAB-NQ-225")
        self.assertEqual(len(data["compatible_components"]), 1)
        comp = data["compatible_components"][0]
        self.assertEqual(comp["sku"], "INT-QO-120")
        self.assertEqual(len(comp["accessories"]), 1)
        self.assertEqual(comp["accessories"][0]["sku"], "ACC-AUX-QO")
