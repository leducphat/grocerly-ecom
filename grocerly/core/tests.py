"""Kiểm thử hồi quy cho các lỗ hổng nghiệp vụ ở docs/SECURITY.md.

Mỗi test tái hiện đúng kịch bản khai thác mô tả trong tài liệu, để nếu sau này có ai
vô tình khôi phục lại code cũ thì test đỏ ngay.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, CartOrderItem, Category, Product, ProductReview, Vendor
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


def deliver_order(user, product, status='delivered'):
    """Dựng một đơn đã giao chứa `product` — tiền đề của điều kiện đánh giá (A2).

    Dòng hóa đơn mang **khóa ngoại** tới sản phẩm, đúng cách `save_checkout_info` tạo ra
    từ PLAN bước 2.11 (ADR-0006). Chính khóa ngoại này là thứ `has_purchased` tra.
    """
    order = CartOrder.objects.create(
        user=user, price=product.price, product_status=status, paid_status=True,
    )
    CartOrderItem.objects.create(
        order=order,
        product=product,
        invoice_no=f"INVOICE_NO-{order.id}",
        item=product.title,
        image="/media/products.jpg",
        quantity=1,
        price=product.price,
        total=product.price,
    )
    return order


class AddReviewTests(TestCase):
    """S-08 / A2 — chốt chặn đánh giá phải nằm ở server, không chỉ ở template."""

    def setUp(self):
        self.product = Product.objects.create(title="Sữa tươi", product_status='published')
        self.user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau-kho-doan",
        )
        self.url = reverse("core:ajax-add-review", args=[self.product.id])
        # Từ PLAN bước 2.12 (A2 / UC 3.2.14) đánh giá đòi hỏi đã mua hàng, nên nhóm test
        # này phải dựng sẵn một đơn đã giao. Điều kiện đó có test riêng ở
        # `core/test_review_purchase.py`; ở đây nó chỉ là tiền đề.
        deliver_order(self.user, self.product)

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


class EditDeleteReviewTests(TestCase):
    """UC 3.2.14 / Hình 22–23 — báo cáo ghi đích danh `ajax_edit_review`,
    `ajax_delete_review`; trước 2026-08-25 hai hàm này không tồn tại (SPEC-GAPS A1)."""

    def setUp(self):
        self.product = Product.objects.create(title="Sữa tươi", product_status='published')
        self.author = User.objects.create_user(
            username="chu", email="chu@example.com", password="matkhau-kho-doan",
        )
        self.other = User.objects.create_user(
            username="nguoikhac", email="khac@example.com", password="matkhau-kho-doan",
        )
        # Chủ đánh giá phải là người đã mua — `test_can_review_again_after_deleting`
        # gọi lại `ajax_add_review`, mà từ PLAN 2.12 đường đó đòi hỏi có đơn đã giao.
        # Sửa/xóa thì không cần: đánh giá chỉ tồn tại nếu trước đó đã mua rồi.
        deliver_order(self.author, self.product)
        self.review = ProductReview.objects.create(
            user=self.author, product=self.product, review="Tạm được", rating=3,
        )
        self.edit_url = reverse("core:ajax-edit-review", args=[self.review.id])
        self.delete_url = reverse("core:ajax-delete-review", args=[self.review.id])

    def test_author_can_edit_own_review(self):
        self.client.force_login(self.author)

        response = self.client.post(self.edit_url, {'review': "Ngon lắm", 'rating': '5'})

        self.assertEqual(response.status_code, 200)
        self.review.refresh_from_db()
        self.assertEqual(self.review.review, "Ngon lắm")
        self.assertEqual(self.review.rating, 5)

    def test_other_user_cannot_edit(self):
        self.client.force_login(self.other)

        response = self.client.post(self.edit_url, {'review': "Bị sửa trộm", 'rating': '1'})

        self.assertEqual(response.status_code, 404)
        self.review.refresh_from_db()
        self.assertEqual(self.review.review, "Tạm được")

    def test_anonymous_cannot_edit(self):
        response = self.client.post(self.edit_url, {'review': "Hack", 'rating': '1'})

        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertEqual(self.review.review, "Tạm được")

    def test_edit_rejects_invalid_rating(self):
        self.client.force_login(self.author)

        response = self.client.post(self.edit_url, {'review': "Ngon", 'rating': '99'})

        self.assertEqual(response.status_code, 400)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 3)

    def test_edit_rejects_get(self):
        self.client.force_login(self.author)

        self.assertEqual(self.client.get(self.edit_url).status_code, 405)

    def test_author_can_delete_own_review(self):
        self.client.force_login(self.author)

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_other_user_cannot_delete(self):
        self.client.force_login(self.other)

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ProductReview.objects.count(), 1)

    def test_can_review_again_after_deleting(self):
        self.client.force_login(self.author)
        self.client.post(self.delete_url)

        response = self.client.post(
            reverse("core:ajax-add-review", args=[self.product.id]),
            {'review': "Đánh giá lại", 'rating': '4'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductReview.objects.count(), 1)

    def test_product_page_shows_controls_only_to_the_author(self):
        self.client.force_login(self.author)
        own = self.client.get(
            reverse("core:product-detail", args=[self.product.p_id])
        ).content.decode()

        self.client.force_login(self.other)
        other = self.client.get(
            reverse("core:product-detail", args=[self.product.p_id])
        ).content.decode()

        self.assertIn('class="edit-review-form-%d' % self.review.id, own)
        self.assertNotIn('class="edit-review-form-%d' % self.review.id, other)
