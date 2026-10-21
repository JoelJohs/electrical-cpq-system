from django.test import TestCase

from quotes.models import Quote, QuoteItem
from quotes.selectors import get_quote_bom
from quotes.tests.conftest import create_sample_electrical_catalog


class BillOfMaterialsGenerationTest(TestCase):
    def setUp(self):
        self.catalog = create_sample_electrical_catalog()
        self.board = self.catalog["board"]
        self.breaker_qo = self.catalog["breaker_qo"]
        self.aux_contact = self.catalog["aux_contact"]

    def test_bom_generation_for_board_assembly(self):
        quote = Quote.objects.create(
            client_name="Cliente Industrial",
            project_reference="Planta Norte",
            is_board_assembly=True,
            board_product=self.board,
        )
        QuoteItem.objects.create(
            quote=quote,
            product=self.breaker_qo,
            quantity=5,
            slot_position=1,
            notes="Circuitos de iluminación",
        )
        QuoteItem.objects.create(
            quote=quote,
            product=self.breaker_qo,
            quantity=3,
            slot_position=7,
            notes="Circuitos de contactos",
        )
        QuoteItem.objects.create(
            quote=quote,
            product=self.aux_contact,
            quantity=2,
            notes="Señalización SCADA",
        )

        bom = get_quote_bom(quote)

        self.assertEqual(bom["folio"], quote.folio)
        self.assertEqual(bom["client_name"], "Cliente Industrial")
        self.assertEqual(bom["project_reference"], "Planta Norte")
        self.assertTrue(bom["is_board_assembly"])
        self.assertIsNotNone(bom["board"])
        self.assertEqual(bom["board"]["sku"], self.board.sku)
        self.assertEqual(bom["board"]["quantity"], 1)

        # 3 partidas detalladas
        self.assertEqual(len(bom["items"]), 3)

        # En aggregated_materials:
        # TAB-NQ-225: 1
        # INT-QO-120: 5 + 3 = 8
        # ACC-AUX-QO: 2
        aggregated = {
            m["sku"]: m["total_quantity"] for m in bom["aggregated_materials"]
        }
        self.assertEqual(aggregated[self.board.sku], 1)
        self.assertEqual(aggregated[self.breaker_qo.sku], 8)
        self.assertEqual(aggregated[self.aux_contact.sku], 2)

        # Conteo total de piezas físicas
        self.assertEqual(bom["total_components_count"], 1 + 8 + 2)

    def test_bom_generation_for_standard_quote(self):
        quote = Quote.objects.create(
            client_name="Mostrador General",
            is_board_assembly=False,
        )
        QuoteItem.objects.create(
            quote=quote,
            product=self.breaker_qo,
            quantity=10,
        )

        bom = get_quote_bom(quote)

        self.assertFalse(bom["is_board_assembly"])
        self.assertIsNone(bom["board"])
        self.assertEqual(len(bom["items"]), 1)
        self.assertEqual(len(bom["aggregated_materials"]), 1)
        self.assertEqual(bom["aggregated_materials"][0]["sku"], self.breaker_qo.sku)
        self.assertEqual(bom["aggregated_materials"][0]["total_quantity"], 10)
        self.assertEqual(bom["total_components_count"], 10)
