from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

from quotes.enums import QuoteStatus
from quotes.models import Quote, QuoteItem, generate_next_folio
from quotes.tests.conftest import create_sample_electrical_catalog


class QuoteModelTest(TestCase):
    def setUp(self):
        self.catalog = create_sample_electrical_catalog()
        self.board = self.catalog["board"]
        self.breaker = self.catalog["breaker_qo"]

    def test_auto_folio_generation(self):
        current_year = datetime.now().year
        quote1 = Quote.objects.create(client_name="Cliente Uno")
        self.assertTrue(quote1.folio.startswith(f"COT-{current_year}-"))
        self.assertEqual(quote1.folio, f"COT-{current_year}-0001")

        quote2 = Quote.objects.create(client_name="Cliente Dos")
        self.assertEqual(quote2.folio, f"COT-{current_year}-0002")

    def test_generate_next_folio_helper(self):
        folio = generate_next_folio()
        self.assertIn("COT-", folio)

    def test_board_assembly_validation_missing_board(self):
        quote = Quote(
            client_name="Cliente Inválido",
            is_board_assembly=True,
            board_product=None,
        )
        with self.assertRaises(ValidationError) as ctx:
            quote.full_clean()
        self.assertIn("board_product", ctx.exception.message_dict)

    def test_board_assembly_validation_invalid_product_type(self):
        quote = Quote(
            client_name="Cliente Inválido",
            is_board_assembly=True,
            board_product=self.breaker,  # COMPONENT, not BOARD
        )
        with self.assertRaises(ValidationError) as ctx:
            quote.full_clean()
        self.assertIn("board_product", ctx.exception.message_dict)

    def test_valid_board_assembly(self):
        quote = Quote.objects.create(
            client_name="Cliente Válido",
            is_board_assembly=True,
            board_product=self.board,
        )
        self.assertEqual(quote.status, QuoteStatus.DRAFT)
        self.assertTrue(quote.can_edit())
        self.assertFalse(quote.is_validated())

    def test_quote_str_representation(self):
        quote = Quote.objects.create(client_name="Constructora Bajío")
        self.assertIn(quote.folio, str(quote))
        self.assertIn("Constructora Bajío", str(quote))


class QuoteItemModelTest(TestCase):
    def setUp(self):
        self.catalog = create_sample_electrical_catalog()
        self.board = self.catalog["board"]
        self.breaker = self.catalog["breaker_qo"]
        self.quote = Quote.objects.create(
            client_name="Cliente Industrial",
            is_board_assembly=True,
            board_product=self.board,
        )

    def test_create_quote_item(self):
        item = QuoteItem.objects.create(
            quote=self.quote,
            product=self.breaker,
            quantity=3,
            slot_position=1,
            notes="Circuito principal",
        )
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.slot_position, 1)
        self.assertIn("INT-QO-120", str(item))
        self.assertIn("Ranura 1", str(item))

    def test_quantity_minimum_validator(self):
        item = QuoteItem(
            quote=self.quote,
            product=self.breaker,
            quantity=0,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_prevent_duplicate_product_same_slot(self):
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.breaker,
            quantity=1,
            slot_position=5,
        )
        duplicate = QuoteItem(
            quote=self.quote,
            product=self.breaker,
            quantity=2,
            slot_position=5,
        )
        with self.assertRaises(ValidationError):
            duplicate.validate_constraints()

    def test_protect_product_deletion_when_in_quote(self):
        QuoteItem.objects.create(
            quote=self.quote,
            product=self.breaker,
            quantity=1,
        )
        with self.assertRaises(ProtectedError):
            self.breaker.delete()

    def test_editing_blocked_on_immutable_quote(self):
        self.quote.status = QuoteStatus.SENT
        self.quote.save()

        item = QuoteItem(
            quote=self.quote,
            product=self.breaker,
            quantity=1,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()
