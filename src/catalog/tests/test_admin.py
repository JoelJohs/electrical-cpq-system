from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from catalog.enums import ProductType
from catalog.models import Product

User = get_user_model()


class CatalogAdminAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="admin_secure_password_123",
        )
        self.product = Product.objects.create(
            sku="TAB-TEST-1",
            name="Tablero de Prueba Admin",
            slug="tab-test-1",
            product_type=ProductType.BOARD,
            specs={},
            is_active=True,
        )

    def test_anonymous_access_redirects_to_login(self):
        response = self.client.get("/admin/catalog/product/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_authenticated_admin_can_access_catalog(self):
        self.client.login(
            username="admin_test",
            password="admin_secure_password_123",
        )
        response = self.client.get("/admin/catalog/product/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TAB-TEST-1")

    def test_admin_product_change_form_renders_inlines(self):
        self.client.login(
            username="admin_test",
            password="admin_secure_password_123",
        )
        response = self.client.get(f"/admin/catalog/product/{self.product.id}/change/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compatibilidades entre Productos")
