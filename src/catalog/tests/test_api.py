from django.test import Client, TestCase

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility


class CatalogAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tablero = Product.objects.create(
            nombre_corto="NQ-225-30P",
            nombre_largo="Tablero Alumbrado NQ 225A 30 Polos",
            descripcion="Tablero de alumbrado tipo NQ",
            is_active=True,
        )
        self.interruptor = Product.objects.create(
            nombre_corto="QO-120",
            nombre_largo="Interruptor Termomagnético QO 1P 20A",
            descripcion="Interruptor enchufable 1P 20A",
            is_active=True,
        )
        self.accesorio = Product.objects.create(
            nombre_corto="AUX-QO",
            nombre_largo="Contacto Auxiliar 1NA/1NC",
            descripcion="Contacto auxiliar de señalización",
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
        self.assertEqual(data["total"], 3)

    def test_search_products(self):
        response = self.client.get("/api/v1/catalog/products/?search=Auxiliar")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["nombre_corto"], "AUX-QO")

    def test_get_product_detail(self):
        response = self.client.get(f"/api/v1/catalog/products/{self.tablero.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["nombre_corto"], "NQ-225-30P")
        self.assertEqual(data["id"], self.tablero.id)

    def test_get_product_detail_404(self):
        response = self.client.get("/api/v1/catalog/products/999999/")
        self.assertEqual(response.status_code, 404)

    def test_get_product_compatibilities(self):
        response = self.client.get(
            f"/api/v1/catalog/products/{self.tablero.id}/compatibilities/"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["product"]["nombre_corto"], "NQ-225-30P")
        self.assertEqual(len(data["compatibilities"]), 1)
        self.assertEqual(data["compatibilities"][0]["target_nombre_corto"], "QO-120")

    def test_get_product_tree(self):
        response = self.client.get(f"/api/v1/catalog/products/{self.tablero.id}/tree/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["product"]["nombre_corto"], "NQ-225-30P")
        self.assertEqual(len(data["compatible_components"]), 1)
        comp = data["compatible_components"][0]
        self.assertEqual(comp["nombre_corto"], "QO-120")

    def test_get_product_tree_bidirectional_api(self):
        response = self.client.get(
            f"/api/v1/catalog/products/{self.interruptor.id}/tree/"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["product"]["nombre_corto"], "QO-120")
        self.assertEqual(len(data["host_equipment"]), 1)
        self.assertEqual(data["host_equipment"][0]["nombre_corto"], "NQ-225-30P")
