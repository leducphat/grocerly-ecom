"""Kiểm thử luồng đăng sản phẩm sau khi bỏ bước duyệt (ADR-0002).

Tương ứng bước 5.3 trong docs/PLAN.md: nhân viên tự quyết trạng thái bằng nút bấm,
không cần Quản trị viên duyệt.
"""

from django.test import TestCase
from django.urls import reverse

from core.models import Product
from userauths.models import User


class AddProductStatusTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username="nhanvien", email="nhanvien@example.com",
            password="matkhau-kho-doan", is_staff=True,
        )
        self.client.force_login(self.staff)
        self.url = reverse("useradmin:dashboard-add-products")

    def _post(self, **overrides):
        data = {
            'title': "Sữa tươi Vinamilk",
            'description': "Sữa tươi tiệt trùng",
            'price': "25000",
            'old_price': "30000",
            'stock_count': "50",
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_publish_button_puts_product_on_sale_without_admin(self):
        self._post(action='publish')

        product = Product.objects.get(title="Sữa tươi Vinamilk")
        self.assertEqual(product.product_status, 'published')

    def test_draft_button_keeps_product_hidden(self):
        self._post(action='save_draft')

        product = Product.objects.get(title="Sữa tươi Vinamilk")
        self.assertEqual(product.product_status, 'draft')

    def test_defaults_to_draft_when_no_action_sent(self):
        self._post()

        product = Product.objects.get(title="Sữa tươi Vinamilk")
        self.assertEqual(product.product_status, 'draft')

    def test_unknown_action_falls_back_to_draft(self):
        self._post(action='published')  # giá trị model, không phải tên nút

        product = Product.objects.get(title="Sữa tươi Vinamilk")
        self.assertEqual(product.product_status, 'draft')


class EditProductStatusTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username="nhanvien", email="nhanvien@example.com",
            password="matkhau-kho-doan", is_staff=True,
        )
        self.client.force_login(self.staff)
        self.product = Product.objects.create(
            title="Sữa tươi", price=25000, old_price=30000,
            stock_count=50, product_status='published',
        )
        self.url = reverse("useradmin:dashboard-edit-products", args=[self.product.p_id])

    def _post(self, **overrides):
        data = {
            'title': self.product.title,
            'description': "Sữa tươi tiệt trùng",
            'price': "25000",
            'old_price': "30000",
            'stock_count': "50",
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_stop_selling_moves_to_disabled(self):
        self._post(action='disable')

        self.product.refresh_from_db()
        self.assertEqual(self.product.product_status, 'disabled')

    def test_plain_save_keeps_current_status(self):
        self._post(title="Sữa tươi ít đường")

        self.product.refresh_from_db()
        self.assertEqual(self.product.product_status, 'published')
        self.assertEqual(self.product.title, "Sữa tươi ít đường")

    def test_publish_button_puts_draft_on_sale(self):
        self.product.product_status = 'draft'
        self.product.save()

        self._post(action='publish')

        self.product.refresh_from_db()
        self.assertEqual(self.product.product_status, 'published')
