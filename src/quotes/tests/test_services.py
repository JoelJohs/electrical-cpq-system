from django.core.exceptions import ValidationError
from django.test import TestCase

from quotes.enums import QuoteStatus
from quotes.selectors import (
    get_quote_by_folio,
    get_quote_by_id,
    get_quote_items,
    get_quote_suggested_complements,
    list_quotes,
)
from quotes.services import (
    QuoteStateError,
    add_item_to_quote,
    create_quote,
    remove_quote_item,
    update_quote_item,
)
from quotes.tests.conftest import create_sample_electrical_catalog


class QuoteServicesAndSelectorsTest(TestCase):
    def setUp(self):
        self.catalog = create_sample_electrical_catalog()
        self.board = self.catalog["board"]
        self.breaker = self.catalog["breaker_qo"]
        self.aux_contact = self.catalog["aux_contact"]
        self.lug_kit = self.catalog["lug_kit"]

    def test_create_simple_quote(self):
        quote = create_quote(
            client_name="Cliente General",
            project_reference="Proyecto Iluminación",
            notes="Entrega en sucursal",
        )
        self.assertEqual(quote.client_name, "Cliente General")
        self.assertEqual(quote.status, QuoteStatus.DRAFT)
        self.assertFalse(quote.is_board_assembly)
        self.assertIsNone(quote.board_product)

    def test_create_board_assembly_quote(self):
        quote = create_quote(
            client_name="Ingeniería Moreliana",
            is_board_assembly=True,
            board_sku="TAB-NQ-225",
        )
        self.assertTrue(quote.is_board_assembly)
        self.assertEqual(quote.board_product, self.board)

    def test_create_board_assembly_missing_sku_fails(self):
        with self.assertRaises(ValidationError):
            create_quote(
                client_name="Cliente Error",
                is_board_assembly=True,
                board_sku=None,
            )

    def test_create_board_assembly_non_existent_sku_fails(self):
        with self.assertRaises(ValidationError):
            create_quote(
                client_name="Cliente Error",
                is_board_assembly=True,
                board_sku="NO-EXISTE",
            )

    def test_add_item_to_quote_success(self):
        quote = create_quote(client_name="Cliente Partidas")
        item = add_item_to_quote(
            quote=quote,
            product_sku="INT-QO-120",
            quantity=5,
            slot_position=1,
            notes="Circuito principal",
        )
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.product, self.breaker)

        items = get_quote_items(quote)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].quantity, 5)

    def test_add_item_duplicate_slot_increments_quantity(self):
        quote = create_quote(client_name="Cliente Partidas")
        add_item_to_quote(
            quote=quote,
            product_sku="INT-QO-120",
            quantity=2,
            slot_position=1,
        )
        item2 = add_item_to_quote(
            quote=quote,
            product_sku="INT-QO-120",
            quantity=3,
            slot_position=1,
        )
        self.assertEqual(item2.quantity, 5)
        items = get_quote_items(quote)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].quantity, 5)

    def test_add_item_to_validated_quote_reverts_to_draft(self):
        quote = create_quote(client_name="Cliente Validado")
        quote.status = QuoteStatus.VALIDATED
        quote.save()

        add_item_to_quote(quote=quote, product_sku="INT-QO-120", quantity=1)
        quote.refresh_from_db()
        self.assertEqual(quote.status, QuoteStatus.DRAFT)

    def test_add_item_to_sent_quote_raises_error(self):
        quote = create_quote(client_name="Cliente Emitido")
        quote.status = QuoteStatus.SENT
        quote.save()

        with self.assertRaises(QuoteStateError):
            add_item_to_quote(quote=quote, product_sku="INT-QO-120", quantity=1)

    def test_update_quote_item(self):
        quote = create_quote(client_name="Cliente Update")
        item = add_item_to_quote(quote=quote, product_sku="INT-QO-120", quantity=2)

        updated = update_quote_item(item_id=item.id, quantity=10, notes="Actualizado")
        self.assertEqual(updated.quantity, 10)
        self.assertEqual(updated.notes, "Actualizado")

    def test_remove_quote_item(self):
        quote = create_quote(client_name="Cliente Remove")
        item = add_item_to_quote(quote=quote, product_sku="INT-QO-120", quantity=2)

        quote_id = remove_quote_item(item_id=item.id)
        self.assertEqual(quote_id, quote.id)
        self.assertEqual(len(get_quote_items(quote)), 0)

    def test_selectors_by_id_and_folio(self):
        quote = create_quote(
            client_name="Cliente Selector", project_reference="Torre A"
        )
        by_id = get_quote_by_id(quote.id)
        self.assertIsNotNone(by_id)
        self.assertEqual(by_id.client_name, "Cliente Selector")

        by_folio = get_quote_by_folio(quote.folio)
        self.assertIsNotNone(by_folio)
        self.assertEqual(by_folio.id, quote.id)

        listed = list_quotes(client_name="Selector")
        self.assertEqual(len(listed), 1)

    def test_get_quote_suggested_complements(self):
        # Cotización de tablero con un interruptor
        quote = create_quote(
            client_name="Cliente Tablero",
            is_board_assembly=True,
            board_sku="TAB-NQ-225",
        )
        add_item_to_quote(quote=quote, product_sku="INT-QO-120", quantity=1)

        # Debe sugerir KIT-ZAP-225 (del tablero) y ACC-AUX-QO (del interruptor)
        suggestions = get_quote_suggested_complements(quote)
        suggested_skus = {s["sku"] for s in suggestions}
        self.assertIn("KIT-ZAP-225", suggested_skus)
        self.assertIn("ACC-AUX-QO", suggested_skus)

        # Si ya agregamos KIT-ZAP-225 a la cotización, ya no debe sugerirse
        add_item_to_quote(quote=quote, product_sku="KIT-ZAP-225", quantity=1)
        suggestions_after = get_quote_suggested_complements(quote)
        suggested_skus_after = {s["sku"] for s in suggestions_after}
        self.assertNotIn("KIT-ZAP-225", suggested_skus_after)
        self.assertIn("ACC-AUX-QO", suggested_skus_after)

    def test_transition_quote_status_lifecycle(self):
        from quotes.services import transition_quote_status

        quote = create_quote(
            client_name="Ciclo de Vida",
            is_board_assembly=True,
            board_sku="TAB-NQ-225",
        )
        # Intentar validar sin partidas debe fallar
        with self.assertRaises(ValidationError):
            transition_quote_status(quote, QuoteStatus.VALIDATED)

        # Agregar partida válida
        add_item_to_quote(quote=quote, product_sku="INT-QO-120", quantity=5)

        # Transicionar a VALIDATED
        q_val = transition_quote_status(
            quote, QuoteStatus.VALIDATED, reason="Revisión de ingeniería aprobada"
        )
        self.assertEqual(q_val.status, QuoteStatus.VALIDATED)
        self.assertIn("Revisión de ingeniería", q_val.notes)

        # Transicionar a SENT
        q_sent = transition_quote_status(quote, QuoteStatus.SENT)
        self.assertEqual(q_sent.status, QuoteStatus.SENT)

        # Transicionar a ACCEPTED
        q_acc = transition_quote_status(quote, QuoteStatus.ACCEPTED)
        self.assertEqual(q_acc.status, QuoteStatus.ACCEPTED)

        # Intentar transicionar desde ACCEPTED debe fallar
        with self.assertRaises(QuoteStateError):
            transition_quote_status(quote, QuoteStatus.DRAFT)
