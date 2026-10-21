from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase

from config.urls import health_check


class HealthCheckViewUnitTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_health_check_view_function(self):
        request = self.factory.get("/health/")
        response = health_check(request)

        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"status": "ok"}')
        self.assertEqual(response["Content-Type"], "application/json")
