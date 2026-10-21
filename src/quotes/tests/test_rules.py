from django.test import TestCase

from catalog.enums import RelationshipType
from catalog.models import Product, ProductCompatibility
from quotes.models import Quote, QuoteItem
from quotes.rules import validate_quote_configuration
from quotes.tests.conftest import create_sample_electrical_catalog


class TechnicalValidationEngineTest(TestCase):
    def setUp(self):
        self.catalog = create_sample_electrical_catalog()
        self.board = self.catalog["board"]  # 30 espacios, 225A
        self.breaker_qo = self.catalog["breaker_qo"]  # 1 polo, 20A, enchufable
        self.breaker_edb = self.catalog["breaker_edb"]  # 3 polos, 100A, atornillable
        self.aux_contact = self.catalog["aux_contact"]

        self.quote = Quote.objects.create(
            client_name="Test Tablero",
            is_board_assembly=True,
            board_product=self.board,
        )

    def test_valid_board_configuration(self):
        # 10 interruptores de 1 polo = 10 polos en tablero de 30 polos
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.breaker_qo,
            quantity=10,
        )
        res = validate_quote_configuration(self.quote)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertEqual(res["summary"]["total_slots_capacity"], 30)
        self.assertEqual(res["summary"]["occupied_slots"], 10)
        self.assertEqual(res["summary"]["available_slots"], 20)

    def test_insufficient_space_error(self):
        # 35 interruptores de 1 polo = 35 polos > 30 polos
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.breaker_qo,
            quantity=35,
        )
        res = validate_quote_configuration(self.quote)
        self.assertFalse(res["valid"])
        error_codes = [e["code"] for e in res["errors"]]
        self.assertIn("INSUFFICIENT_SPACE", error_codes)
        error = next(e for e in res["errors"] if e["code"] == "INSUFFICIENT_SPACE")
        self.assertEqual(error["details"]["overflow"], 5)
        self.assertEqual(error["details"]["required_spaces"], 35)

    def test_incompatible_derivative_mounting_error(self):
        # breaker_edb no tiene arista COMPATIBLE_WITH desde TAB-NQ-225
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.breaker_edb,
            quantity=1,
        )
        res = validate_quote_configuration(self.quote)
        self.assertFalse(res["valid"])
        error_codes = [e["code"] for e in res["errors"]]
        self.assertIn("INCOMPATIBLE_DERIVATIVE", error_codes)

    def test_amperage_exceeded_error(self):
        # Crear un interruptor gigante de 300A en tablero de 225A
        giant_breaker = Product.objects.create(
            sku="INT-GIANT-300",
            name="Interruptor Gigante 300A",
            slug="int-giant-300",
            specs={"polos": 3, "amperaje": 300},
        )
        ProductCompatibility.objects.create(
            source=self.board,
            target=giant_breaker,
            relationship_type=RelationshipType.COMPATIBLE_WITH,
        )
        QuoteItem.objects.create(
            quote=self.quote,
            product=giant_breaker,
            quantity=1,
        )
        res = validate_quote_configuration(self.quote)
        self.assertFalse(res["valid"])
        error_codes = [e["code"] for e in res["errors"]]
        self.assertIn("AMPERAGE_EXCEEDED", error_codes)

    def test_missing_required_accessory_error(self):
        # Crear una arista REQUIRES: breaker_qo REQUIRES aux_contact
        ProductCompatibility.objects.create(
            source=self.breaker_qo,
            target=self.aux_contact,
            relationship_type=RelationshipType.REQUIRES,
        )
        # Añadimos solo el interruptor sin el contacto auxiliar
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.breaker_qo,
            quantity=1,
        )
        res = validate_quote_configuration(self.quote)
        self.assertFalse(res["valid"])
        error_codes = [e["code"] for e in res["errors"]]
        self.assertIn("MISSING_REQUIRED_ACCESSORY", error_codes)

        # Ahora agregamos el contacto auxiliar requerido
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.aux_contact,
            quantity=1,
        )
        res_after = validate_quote_configuration(self.quote)
        self.assertTrue(res_after["valid"])
        self.assertEqual(len(res_after["errors"]), 0)

    def test_requires_cycle_prevention_does_not_crash(self):
        # A requiere B y B requiere A
        ProductCompatibility.objects.create(
            source=self.breaker_qo,
            target=self.aux_contact,
            relationship_type=RelationshipType.REQUIRES,
        )
        ProductCompatibility.objects.create(
            source=self.aux_contact,
            target=self.breaker_qo,
            relationship_type=RelationshipType.REQUIRES,
        )
        # Ambos agregados a la cotización
        QuoteItem.objects.create(quote=self.quote, product=self.breaker_qo, quantity=1)
        QuoteItem.objects.create(quote=self.quote, product=self.aux_contact, quantity=1)

        # No debe entrar en bucle infinito
        res = validate_quote_configuration(self.quote)
        self.assertTrue(res["valid"])
