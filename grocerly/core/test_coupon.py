"""Áp mã giảm giá ở trang thanh toán — PLAN bước 2.9, SPEC-GAPS A6 (UC 3.2.21).

Trước file này, nhánh áp mã trong `checkout()` **không có một test HTTP nào**: hai test
duy nhất chạm tới `Coupon` (`test_checkout.py`, `test_softdelete.py`) đều ở tầng model.
Nên nửa đầu file là lưới an toàn cho hành vi đã có, nửa sau mới là chức năng mới.

`CouponGuardTests` là chỗ vá **lỗ hổng thật đang mở**, phát hiện khi rà lại bước 2.10:
`place_cod_order` và `vnpay_payment` đều từ chối đơn đã hủy, nhưng `checkout()` — chính
là trang áp mã — thì không. Và đơn COD đã đặt vẫn có `paid_status=False` cho tới lúc
giao hàng, nên chốt `paid_status` sẵn có cũng không chặn được nó.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, CartOrderItem, Category, Coupon, Product, Vendor
from userauths.models import User


class CouponTestCase(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(self.customer)

        self.category = Category.objects.create(title="Trái cây")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("100000.00"), stock_count=10,
            product_status='published', category=self.category, vendor=self.vendor,
        )
        self.order = self.make_order()
        self.coupon = Coupon.objects.create(code="GIAM10", discount=10, active=True)

    def make_order(self, price=Decimal("100000.00"), **kwargs):
        order = CartOrder.objects.create(user=self.customer, price=price, **kwargs)
        CartOrderItem.objects.create(
            order=order, product=self.product,
            invoice_no=f"INVOICE_NO-{order.id}", item=self.product.title,
            image="/media/products.jpg", quantity=1,
            price=self.product.price, total=self.product.price,
        )
        return order

    def apply(self, code="GIAM10", order=None):
        order = order or self.order
        return self.client.post(
            reverse("core:checkout", args=[order.oid]), {'code': code}
        )

    def price_of(self, order=None):
        order = order or self.order
        order.refresh_from_db()
        return order.price


class CouponBasicsTests(CouponTestCase):
    """Lưới an toàn cho ba nhánh vốn đã có nhưng chưa từng được test qua HTTP."""

    def test_a_valid_coupon_lowers_the_order_price(self):
        self.apply()

        self.assertEqual(self.price_of(), Decimal("90000.00"))
        self.assertEqual(self.order.coupons.count(), 1)

    def test_the_discount_is_recorded_as_savings(self):
        self.apply()
        self.order.refresh_from_db()

        self.assertEqual(self.order.saved, Decimal("10000.00"))

    def test_applying_the_same_coupon_twice_is_rejected(self):
        self.apply()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("90000.00"))
        self.assertEqual(self.order.coupons.count(), 1)

    def test_an_unknown_code_changes_nothing(self):
        self.apply(code="KHONGCOTHAT")

        self.assertEqual(self.price_of(), Decimal("100000.00"))
        self.assertEqual(self.order.coupons.count(), 0)

    def test_an_inactive_coupon_is_rejected(self):
        self.coupon.active = False
        self.coupon.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))

    def test_the_checkout_view_rejects_a_soft_deleted_coupon(self):
        """Gọi **view thật**, không chép lại truy vấn.

        `test_softdelete.py` chốt rằng `Coupon.objects.filter(...)` bỏ qua mã đã xóa mềm,
        nhưng nó tự dựng lại truy vấn đó trong test. Đổi `objects` thành `all_objects`
        trong view thì test kia vẫn xanh còn hành vi đã lệch — test này thì đỏ.
        """
        self.coupon.soft_delete()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))
        self.assertEqual(self.order.coupons.count(), 0)


class CouponGuardTests(CouponTestCase):
    """Lỗ hổng thật, phát hiện khi rà lại bước 2.10."""

    def test_a_cancelled_order_rejects_a_coupon(self):
        """`checkout()` là trang áp mã mà lại thiếu đúng chốt chặn của 2.10."""
        self.order.product_status = 'cancelled'
        self.order.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))
        self.assertEqual(self.order.coupons.count(), 0)

    def test_a_cancelled_order_does_not_even_render_the_checkout_page(self):
        self.order.product_status = 'cancelled'
        self.order.save()

        response = self.client.get(reverse("core:checkout", args=[self.order.oid]))

        self.assertEqual(response.status_code, 302)

    def test_a_placed_cod_order_rejects_a_coupon(self):
        """Đơn COD đã đặt: hàng đang xử lý nhưng `paid_status` vẫn `False`.

        Chốt `paid_status` sẵn có không đỡ được, nên trước bước này khách đặt COD xong
        quay lại `/checkout/<oid>/` là hạ giá được một đơn đang giao.
        """
        self.client.post(reverse("core:place-cod-order", args=[self.order.oid]))

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))
        self.assertEqual(self.order.coupons.count(), 0)

    def test_a_paid_order_rejects_a_coupon(self):
        self.order.paid_status = True
        self.order.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))

    def test_another_customers_order_cannot_be_discounted(self):
        stranger = User.objects.create_user(
            username="nguoila", email="nguoila@example.com", password="matkhau123",
        )
        self.client.force_login(stranger)

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))
