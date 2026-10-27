from django.test import Client, TestCase

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility


class CatalogViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.tablero = Product.objects.create(
            nombre_corto="NQ-225",
            nombre_largo="Tablero Alumbrado NQ 225A",
            descripcion="Tablero base para pruebas",
            is_active=True,
        )
        self.breaker = Product.objects.create(
            nombre_corto="QO-120",
            nombre_largo="Interruptor QO 1P 20A",
            descripcion="Interruptor compatible",
            is_active=True,
        )
        ProductCompatibility.objects.create(
            source=self.tablero,
            target=self.breaker,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
            score=100,
        )

    def test_explorer_view_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asistente de Compatibilidad Eléctrica")
        self.assertContains(response, "NQ-225")
        self.assertContains(response, "ABV ELECTRIC SUPPLY")

    def test_product_tree_json_view(self):
        response = self.client.get(f"/api/products/{self.tablero.id}/tree/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Cache-Control", response.headers)
        self.assertIn("max-age=120", response.headers["Cache-Control"])
        data = response.json()
        self.assertEqual(data["product"]["nombre_corto"], "NQ-225")
        self.assertEqual(len(data["compatible_components"]), 1)
        self.assertEqual(data["compatible_components"][0]["nombre_corto"], "QO-120")

    def test_explorer_view_caching(self):
        """Verifica que explorer_view use la caché para evitar saturación de la BD."""
        from django.core.cache import cache
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        cache.clear()

        # Primer render: consulta la BD
        with CaptureQueriesContext(connection) as ctx1:
            resp1 = self.client.get("/")
        self.assertEqual(resp1.status_code, 200)
        self.assertGreater(len(ctx1), 0)

        # Segundo render: debe servirse de caché de conteo e ítems iniciales
        with CaptureQueriesContext(connection) as ctx2:
            resp2 = self.client.get("/")
        self.assertEqual(resp2.status_code, 200)
        # Consultas drásticamente menores o cero para catálogo
        self.assertLess(len(ctx2), len(ctx1))

    def test_product_tree_json_404(self):
        response = self.client.get("/api/products/999999/tree/")
        self.assertEqual(response.status_code, 404)

    def test_view_renders_panel_capacity_elements(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # Elementos del medidor reactivo de capacidad y advertencias
        self.assertContains(response, "occupiedSlots")
        self.assertContains(response, "isPanelOverloaded")
        self.assertContains(response, "Capacidad de ranuras")
