from django.test import Client, TestCase

from quotes.models import Quote, QuoteItem
from quotes.tests.conftest import create_sample_electrical_catalog


class QuoteViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.catalog = create_sample_electrical_catalog()
        self.board = self.catalog["board"]
        self.breaker_qo = self.catalog["breaker_qo"]

    def test_quote_list_view_renders(self):
        Quote.objects.create(client_name="Cliente A")
        Quote.objects.create(client_name="Cliente B")

        res = self.client.get("/quotes/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Cliente A")
        self.assertContains(res, "Cliente B")
        self.assertContains(res, "ABV ELECTRIC SUPPLY")

    def test_quick_quote_view_renders(self):
        res = self.client.get("/quotes/new/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Nueva Cotización")
        self.assertContains(res, "TAB-NQ-225")

    def test_configurator_view_renders(self):
        quote = Quote.objects.create(
            client_name="Cliente Tablero",
            is_board_assembly=True,
            board_product=self.board,
        )
        QuoteItem.objects.create(
            quote=quote,
            product=self.breaker_qo,
            quantity=2,
            slot_position=1,
        )

        res = self.client.get(f"/quotes/{quote.id}/configurator/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, quote.folio)
        self.assertContains(res, self.board.name)
        self.assertContains(res, "Capacidad de Espacios")

    def test_bom_detail_view_renders(self):
        quote = Quote.objects.create(
            client_name="Cliente Taller",
            is_board_assembly=True,
            board_product=self.board,
        )
        QuoteItem.objects.create(
            quote=quote,
            product=self.breaker_qo,
            quantity=5,
        )

        res = self.client.get(f"/quotes/{quote.id}/bom/")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Lista de Materiales")
        self.assertContains(res, quote.folio)
        self.assertContains(res, self.breaker_qo.sku)
