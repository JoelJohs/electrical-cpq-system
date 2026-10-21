import json

from django.test import Client, TestCase

from quotes.enums import QuoteStatus
from quotes.models import Quote, QuoteItem
from quotes.tests.conftest import create_sample_electrical_catalog


class QuoteAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.catalog = create_sample_electrical_catalog()
        self.board = self.catalog["board"]
        self.breaker_qo = self.catalog["breaker_qo"]
        self.aux_contact = self.catalog["aux_contact"]

    def test_create_quote_success(self):
        payload = {
            "client_name": "Ingeniería y Construcción SA",
            "project_reference": "Nave Industrial B",
            "is_board_assembly": True,
            "board_sku": "TAB-NQ-225",
            "notes": "Entrega prioritaria",
        }
        res = self.client.post(
            "/api/v1/quotes/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["client_name"], "Ingeniería y Construcción SA")
        self.assertEqual(data["project_reference"], "Nave Industrial B")
        self.assertTrue(data["is_board_assembly"])
        self.assertEqual(data["board_sku"], "TAB-NQ-225")
        self.assertEqual(data["status"], QuoteStatus.DRAFT)
        self.assertTrue(data["folio"].startswith("COT-"))

    def test_create_quote_invalid_board(self):
        payload = {
            "client_name": "Test Cliente",
            "is_board_assembly": True,
            "board_sku": "SKU-INEXISTENTE",
        }
        res = self.client.post(
            "/api/v1/quotes/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 400)

    def test_get_quote_by_id_and_not_found(self):
        quote = Quote.objects.create(client_name="Cliente Consulta")
        res = self.client.get(f"/api/v1/quotes/{quote.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["client_name"], "Cliente Consulta")

        res_404 = self.client.get("/api/v1/quotes/999999/")
        self.assertEqual(res_404.status_code, 404)

    def test_add_update_and_delete_quote_item(self):
        quote = Quote.objects.create(
            client_name="Cliente Ensamble",
            is_board_assembly=True,
            board_product=self.board,
        )

        # 1. Agregar partida
        add_payload = {
            "product_sku": "INT-QO-120",
            "quantity": 3,
            "slot_position": 1,
            "notes": "Alumbrado pasillo",
        }
        res_add = self.client.post(
            f"/api/v1/quotes/{quote.id}/items/",
            data=json.dumps(add_payload),
            content_type="application/json",
        )
        self.assertEqual(res_add.status_code, 201)
        data_add = res_add.json()
        self.assertEqual(len(data_add["items"]), 1)
        item_id = data_add["items"][0]["id"]
        self.assertEqual(data_add["items"][0]["quantity"], 3)

        # 2. Actualizar partida
        update_payload = {"quantity": 5}
        res_update = self.client.patch(
            f"/api/v1/quotes/{quote.id}/items/{item_id}/",
            data=json.dumps(update_payload),
            content_type="application/json",
        )
        self.assertEqual(res_update.status_code, 200)
        data_update = res_update.json()
        self.assertEqual(data_update["items"][0]["quantity"], 5)

        # 3. Eliminar partida
        res_del = self.client.delete(f"/api/v1/quotes/{quote.id}/items/{item_id}/")
        self.assertEqual(res_del.status_code, 200)
        data_del = res_del.json()
        self.assertEqual(len(data_del["items"]), 0)

    def test_validate_quote_endpoint(self):
        quote = Quote.objects.create(
            client_name="Cliente Validación",
            is_board_assembly=True,
            board_product=self.board,
        )
        QuoteItem.objects.create(quote=quote, product=self.breaker_qo, quantity=2)

        res = self.client.post(f"/api/v1/quotes/{quote.id}/validate/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["summary"]["total_slots_capacity"], 30)
        self.assertEqual(data["summary"]["occupied_slots"], 2)

    def test_get_bom_endpoint(self):
        quote = Quote.objects.create(
            client_name="Cliente BOM",
            is_board_assembly=True,
            board_product=self.board,
        )
        QuoteItem.objects.create(quote=quote, product=self.breaker_qo, quantity=4)

        res = self.client.get(f"/api/v1/quotes/{quote.id}/bom/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["folio"], quote.folio)
        self.assertEqual(data["board"]["sku"], self.board.sku)
        self.assertEqual(len(data["aggregated_materials"]), 2)

    def test_transition_quote_status_and_immutability(self):
        quote = Quote.objects.create(
            client_name="Cliente Transición",
            is_board_assembly=True,
            board_product=self.board,
        )
        QuoteItem.objects.create(quote=quote, product=self.breaker_qo, quantity=2)

        # Transicionar a VALIDATED
        res_val = self.client.post(
            f"/api/v1/quotes/{quote.id}/transition/",
            data=json.dumps({"target_status": QuoteStatus.VALIDATED}),
            content_type="application/json",
        )
        self.assertEqual(res_val.status_code, 200)
        self.assertEqual(res_val.json()["status"], QuoteStatus.VALIDATED)

        # Transicionar a SENT
        res_sent = self.client.post(
            f"/api/v1/quotes/{quote.id}/transition/",
            data=json.dumps({"target_status": QuoteStatus.SENT}),
            content_type="application/json",
        )
        self.assertEqual(res_sent.status_code, 200)

        # Transicionar a ACCEPTED
        res_acc = self.client.post(
            f"/api/v1/quotes/{quote.id}/transition/",
            data=json.dumps({"target_status": QuoteStatus.ACCEPTED}),
            content_type="application/json",
        )
        self.assertEqual(res_acc.status_code, 200)

        # En estado ACCEPTED, intentar agregar una partida debe retornar 409 Conflict
        res_mod = self.client.post(
            f"/api/v1/quotes/{quote.id}/items/",
            data=json.dumps({"product_sku": "INT-QO-120", "quantity": 1}),
            content_type="application/json",
        )
        self.assertEqual(res_mod.status_code, 409)
