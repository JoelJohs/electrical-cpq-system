from django.test import Client, TestCase


class HealthEndpointIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_returns_200_and_ok_status(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Content-Type"], "application/json")

    def test_health_check_head_request(self):
        response = self.client.head("/health/")
        self.assertEqual(response.status_code, 200)
