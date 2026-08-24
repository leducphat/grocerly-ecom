"""Kiểm thử hồi quy cho các lỗ hổng nghiệp vụ ở docs/SECURITY.md.

Mỗi test tái hiện đúng kịch bản khai thác mô tả trong tài liệu, để nếu sau này có ai
vô tình khôi phục lại code cũ thì test đỏ ngay.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, Category, Product, ProductReview, Vendor
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


class DraftProductVisibilityTests(TestCase):
    """ADR-0002 / PLAN 5.1 — hàng nháp không được lọt ra storefront."""

    def setUp(self):
        self.category = Category.objects.create(title="Trái cây")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        common = dict(category=self.category, vendor=self.vendor, featured=True)
        self.published = Product.objects.create(
            title="Dưa hấu đỏ", product_status='published', **common
        )
        self.draft = Product.objects.create(
            title="Dưa hấu vàng", product_status='draft', **common
        )
        self.disabled = Product.objects.create(
            title="Dưa hấu xanh", product_status='disabled', **common
        )

    def test_published_manager_returns_only_published(self):
        self.assertEqual(list(Product.objects.published()), [self.published])

    def test_draft_hidden_from_search(self):
        response = self.client.get(reverse("core:search"), {'q': "Dưa hấu"})

        self.assertContains(response, "Dưa hấu đỏ")
        self.assertNotContains(response, "Dưa hấu vàng")
        self.assertNotContains(response, "Dưa hấu xanh")

    def test_draft_hidden_from_category_page(self):
        response = self.client.get(
            reverse("core:category-product-list", args=[self.category.c_id])
        )

        self.assertContains(response, "Dưa hấu đỏ")
        self.assertNotContains(response, "Dưa hấu vàng")

    def test_draft_cannot_be_added_to_cart(self):
        response = self.client.get(reverse("core:add-to-cart"), {
            'id': self.draft.id, 'qty': 1,
        })

        self.assertEqual(response.status_code, 404)


class ProductStatusMigrationTests(TestCase):
    """PLAN 5.4 — dữ liệu cũ chuyển sang trạng thái ẩn tương đương, không tự lên sàn."""

    def test_forwards_maps_old_statuses(self):
        import importlib

        from django.apps import apps as global_apps

        # Tên module bắt đầu bằng số nên không import bằng cú pháp `from ... import`.
        migration = importlib.import_module(
            'core.migrations.0005_product_status_drop_review_flow'
        )

        # `choices` không được ép ở tầng DB nên vẫn tạo được giá trị cũ để kiểm thử.
        in_review = Product.objects.create(title="Cũ chờ duyệt", product_status='in_review')
        rejected = Product.objects.create(title="Cũ bị từ chối", product_status='rejected')
        published = Product.objects.create(title="Đang bán", product_status='published')
        draft = Product.objects.create(title="Nháp", product_status='draft')

        # Lưu ý: `apps` thật trả về manager có lọc soft-delete, còn model lịch sử trong
        # migration dùng Manager thường. Test này vì vậy chỉ phủ bản ghi chưa xóa mềm.
        migration.forwards(global_apps, None)

        for product, expected in [
            (in_review, 'draft'),
            (rejected, 'disabled'),
            (published, 'published'),
            (draft, 'draft'),
        ]:
            product.refresh_from_db()
            self.assertEqual(product.product_status, expected, product.title)
