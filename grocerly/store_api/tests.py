"""Kiểm thử rò rỉ hàng nháp qua API công khai và chatbot — SECURITY.md S-04.

Tương ứng bước 5.2 trong docs/PLAN.md.
"""

from django.test import TestCase

from core.models import Product
from store_api.views import get_bestsellers, search_products


class DraftLeakTests(TestCase):

    def setUp(self):
        self.published = Product.objects.create(
            title="Dưa hấu đỏ", product_status='published', featured=True,
        )
        self.draft = Product.objects.create(
            title="Dưa hấu vàng", product_status='draft', featured=True,
        )
        self.disabled = Product.objects.create(
            title="Dưa hấu xanh", product_status='disabled', featured=True,
        )

    def test_product_list_api_hides_unpublished(self):
        response = self.client.get("/api/v1/products/")

        titles = [item['title'] for item in response.json()]
        self.assertEqual(titles, ["Dưa hấu đỏ"])

    def test_chatbot_search_hides_unpublished(self):
        results = search_products("Dưa hấu")

        titles = [item.get('title') for item in results]
        self.assertEqual(titles, ["Dưa hấu đỏ"])

    def test_chatbot_bestsellers_hide_unpublished(self):
        results = get_bestsellers()

        titles = [item['title'] for item in results]
        self.assertEqual(titles, ["Dưa hấu đỏ"])
