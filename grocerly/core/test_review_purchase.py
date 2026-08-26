"""Điều kiện "đã mua mới được đánh giá" — PLAN bước 2.12, SPEC-GAPS A2.

Neo trong báo cáo: **UC 3.2.14 Pre-Conditions** và **Hình 21**. Đây là gap nhóm A mà báo
cáo đã đặc tả sẵn cả use case lẫn lược đồ tuần tự — đóng nó không phải sửa báo cáo.

Điều kiện này từng bị hoãn ở [ADR-0005](../../docs/DECISIONS.md) vì `CartOrderItem` chỉ
lưu **tên** sản phẩm: đổi tên sản phẩm sau khi bán là người mua thật mất quyền đánh giá.
[ADR-0006](../../docs/DECISIONS.md) đảo lại quyết định đó bằng cách thêm khóa ngoại
(bước 2.11), nên nhóm `RenameAndDeleteTests` bên dưới chính là lý do việc này khả thi.

⚠️ Kiểm ở **server**, không chỉ ẩn form. S-08 đã cho thấy chốt chặn nằm mỗi ở template
thì POST thẳng vào endpoint là đi qua được — đó là bài học cũ, không phải giả định.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import (
    CartOrder, CartOrderItem, Category, Product, ProductReview, Vendor,
)
from userauths.models import User


class ReviewPurchaseTestCase(TestCase):

    def setUp(self):
        self.category = Category.objects.create(title="Sữa")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        self.product = Product.objects.create(
            title="Sữa tươi", price=Decimal("30000.00"), product_status='published',
            category=self.category, vendor=self.vendor,
        )
        self.buyer = User.objects.create_user(
            username="nguoimua", email="nguoimua@example.com", password="matkhau123",
        )
        self.url = reverse("core:ajax-add-review", args=[self.product.id])

    def order_for(self, user, product=None, status='delivered', link=True):
        """Một đơn chứa `product`, dựng đúng cách `save_checkout_info` tạo ra."""
        product = product or self.product
        order = CartOrder.objects.create(
            user=user, price=product.price, product_status=status,
        )
        CartOrderItem.objects.create(
            order=order,
            product=product if link else None,
            invoice_no=f"INVOICE_NO-{order.id}",
            item=product.title,
            image="/media/products.jpg",
            quantity=1,
            price=product.price,
            total=product.price,
        )
        return order

    def review(self, text="Ngon", rating='5'):
        return self.client.post(self.url, {'review': text, 'rating': rating})


class WhoMayReviewTests(ReviewPurchaseTestCase):
    """Ai được đánh giá — UC 3.2.14 Pre-Conditions."""

    def test_a_customer_who_never_bought_it_is_refused(self):
        self.client.force_login(self.buyer)

        response = self.review()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_a_customer_with_a_delivered_order_may_review(self):
        self.order_for(self.buyer, status='delivered')
        self.client.force_login(self.buyer)

        response = self.review()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductReview.objects.count(), 1)

    def test_a_customer_with_a_shipped_order_may_review(self):
        """Báo cáo ghi điều kiện là đơn **Shipped** — đúng nguyên văn use case."""
        self.order_for(self.buyer, status='shipped')
        self.client.force_login(self.buyer)

        self.assertEqual(self.review().status_code, 200)

    def test_an_order_still_being_processed_is_not_enough(self):
        """`processing` là đơn chưa rời kho, còn có thể bị hủy."""
        self.order_for(self.buyer, status='processing')
        self.client.force_login(self.buyer)

        response = self.review()

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_buying_a_different_product_does_not_unlock_this_one(self):
        other = Product.objects.create(
            title="Sữa chua", price=Decimal("10000.00"), product_status='published',
            category=self.category, vendor=self.vendor,
        )
        self.order_for(self.buyer, product=other, status='delivered')
        self.client.force_login(self.buyer)

        self.assertEqual(self.review().status_code, 403)

    def test_someone_elses_order_does_not_unlock_it(self):
        stranger = User.objects.create_user(
            username="nguoila", email="nguoila@example.com", password="matkhau123",
        )
        self.order_for(stranger, status='delivered')
        self.client.force_login(self.buyer)

        self.assertEqual(self.review().status_code, 403)

    def test_an_anonymous_visitor_is_still_redirected_to_login(self):
        """`@login_required` phải chạy TRƯỚC chốt chặn mới, không đổi thành 403."""
        response = self.review()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_the_one_review_per_product_rule_still_applies(self):
        """Chốt chặn mới không được che mất chốt chặn cũ (S-08)."""
        self.order_for(self.buyer)
        self.client.force_login(self.buyer)
        self.review()

        response = self.review(text="Nghĩ lại thấy dở")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ProductReview.objects.count(), 1)


class RenameAndDeleteTests(ReviewPurchaseTestCase):
    """Vì sao A2 chỉ khả thi SAU khi có khóa ngoại — ADR-0005 → ADR-0006.

    ADR-0005 loại điều kiện này với lý do: chỉ so được theo tên, nên nhân viên đổi tên
    sản phẩm là chặn nhầm người mua thật. Nhóm test này chốt lại rằng lý do đó **đã hết
    hiệu lực**.
    """

    def test_renaming_the_product_does_not_take_away_the_right_to_review(self):
        self.order_for(self.buyer)
        self.product.title = "Sữa tươi tiệt trùng"
        self.product.save()
        self.client.force_login(self.buyer)

        self.assertEqual(self.review().status_code, 200)

    def test_a_twin_product_does_not_grant_the_right_to_review(self):
        """Chiều ngược lại: trùng tên không được biến thành mua nhầm sản phẩm."""
        twin = Product.objects.create(
            title="Sữa tươi", price=Decimal("30000.00"), product_status='published',
            category=self.category, vendor=self.vendor,
        )
        self.order_for(self.buyer, product=twin, status='delivered')
        self.client.force_login(self.buyer)

        self.assertEqual(self.review().status_code, 403)

    def test_a_legacy_order_line_without_a_link_does_not_grant_the_right(self):
        """Dòng có từ trước migration 0007 mà backfill không dò ra sản phẩm gốc.

        Ở đây **không** có lưới hứng theo tên, khác `product_has_order_history`. Lý do là
        chiều sai nguy hiểm ngược lại: chỗ kia đoán sai thì cùng lắm giữ thừa dữ liệu,
        còn chỗ này đoán sai là **mở quyền đánh giá cho người chưa mua**.
        """
        self.order_for(self.buyer, status='delivered', link=False)
        self.client.force_login(self.buyer)

        self.assertEqual(self.review().status_code, 403)


class ReviewFormVisibilityTests(ReviewPurchaseTestCase):
    """Trang chi tiết sản phẩm — form và lời giải thích đi kèm."""

    def _page(self):
        return self.client.get(
            reverse("core:product-detail", args=[self.product.p_id])
        )

    def test_a_buyer_sees_the_review_form(self):
        self.order_for(self.buyer)
        self.client.force_login(self.buyer)

        self.assertContains(self._page(), 'id="commentForm"')

    def test_a_non_buyer_sees_no_form(self):
        self.client.force_login(self.buyer)

        self.assertNotContains(self._page(), 'id="commentForm"')

    def test_a_non_buyer_is_told_why_instead_of_seeing_nothing(self):
        """Ẩn form không kèm lý do thì khách tưởng chức năng hỏng."""
        self.client.force_login(self.buyer)

        self.assertContains(self._page(), "bought this product")

    def test_a_buyer_who_already_reviewed_sees_neither_form_nor_the_notice(self):
        """Đã đánh giá rồi thì không được báo nhầm là chưa mua."""
        self.order_for(self.buyer)
        ProductReview.objects.create(
            user=self.buyer, product=self.product, review="Ngon", rating=5,
        )
        self.client.force_login(self.buyer)

        page = self._page()
        self.assertNotContains(page, 'id="commentForm"')
        self.assertNotContains(page, "bought this product")

    def test_the_page_still_renders_for_a_guest(self):
        self.assertEqual(self._page().status_code, 200)
