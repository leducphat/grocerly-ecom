"""Kiểm thử hồi quy cho các lỗ hổng nghiệp vụ ở docs/SECURITY.md.

Mỗi test tái hiện đúng kịch bản khai thác mô tả trong tài liệu, để nếu sau này có ai
vô tình khôi phục lại code cũ thì test đỏ ngay.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, Product, ProductReview
from userauths.models import User


class AddToCartPriceTamperingTests(TestCase):
    """S-02 — giá phải đọc từ database, không nhận từ query string."""

    def setUp(self):
        self.product = Product.objects.create(
            title="Dưa hấu",
            price=Decimal("500000.00"),
            stock_count=10,
            product_status='published',
        )

    def _add(self, **overrides):
        params = {
            'id': self.product.id,
            'pid': self.product.p_id,
            'qty': 1,
            'title': self.product.title,
            'price': self.product.price,
            'image': '/media/products.jpg',
        }
        params.update(overrides)
        return self.client.get(reverse("core:add-to-cart"), params)

    def test_ignores_price_sent_by_client(self):
        response = self._add(price='1', title='Hàng giả')

        self.assertEqual(response.status_code, 200)
        item = self.client.session['cart_data_obj'][str(self.product.id)]
        self.assertEqual(item['price'], 500000.0)
        self.assertEqual(item['title'], "Dưa hấu")

    def test_rejects_unpublished_product(self):
        self.product.product_status = 'draft'
        self.product.save()

        response = self._add()

        self.assertEqual(response.status_code, 404)
        self.assertNotIn('cart_data_obj', self.client.session)

    def test_rejects_quantity_above_stock(self):
        response = self._add(qty=999)

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('cart_data_obj', self.client.session)

    def test_update_cart_rejects_quantity_above_stock(self):
        self._add(qty=1)

        response = self.client.get(reverse("core:update-cart"), {
            'id': self.product.id,
            'qty': 999,
        })

        self.assertEqual(response.status_code, 400)
        item = self.client.session['cart_data_obj'][str(self.product.id)]
        self.assertEqual(item['qty'], 1)


class PaymentCompletedTests(TestCase):
    """S-01 — mở URL payment-completed không được biến đơn chưa trả thành đã trả."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau-kho-doan",
        )
        self.client.force_login(self.user)
        self.order = CartOrder.objects.create(
            user=self.user, price=Decimal("500000.00"), payment_method='online',
        )

    def test_visiting_url_does_not_mark_unpaid_order_as_paid(self):
        response = self.client.get(
            reverse("core:payment-completed", args=[self.order.oid])
        )

        self.order.refresh_from_db()
        self.assertFalse(self.order.paid_status)
        self.assertEqual(response.status_code, 302)

    def test_paid_order_still_renders(self):
        self.order.paid_status = True
        self.order.save()

        response = self.client.get(
            reverse("core:payment-completed", args=[self.order.oid])
        )

        self.assertEqual(response.status_code, 200)

    def test_cod_order_renders_without_payment(self):
        self.order.payment_method = 'cod'
        self.order.save()

        response = self.client.get(
            reverse("core:payment-completed", args=[self.order.oid])
        )

        self.assertEqual(response.status_code, 200)


class AddReviewTests(TestCase):
    """S-08 / A2 — chốt chặn đánh giá phải nằm ở server, không chỉ ở template."""

    def setUp(self):
        self.product = Product.objects.create(title="Sữa tươi", product_status='published')
        self.user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau-kho-doan",
        )
        self.url = reverse("core:ajax-add-review", args=[self.product.id])

    def test_anonymous_cannot_review(self):
        response = self.client.post(self.url, {'review': 'Ngon', 'rating': '5'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_cannot_review_same_product_twice(self):
        self.client.force_login(self.user)
        self.client.post(self.url, {'review': 'Ngon', 'rating': '5'})

        response = self.client.post(self.url, {'review': 'Ngon lắm', 'rating': '5'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ProductReview.objects.count(), 1)

    def test_rejects_rating_outside_choices(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {'review': 'Ngon', 'rating': '99'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_rejects_empty_review(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {'review': '   ', 'rating': '5'})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_accepts_valid_review(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {'review': 'Ngon', 'rating': '5'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductReview.objects.count(), 1)
