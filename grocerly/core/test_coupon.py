"""Áp mã giảm giá ở trang thanh toán — PLAN bước 2.9, SPEC-GAPS A6 (UC 3.2.21).

Trước file này, nhánh áp mã trong `checkout()` **không có một test HTTP nào**: hai test
duy nhất chạm tới `Coupon` (`test_checkout.py`, `test_softdelete.py`) đều ở tầng model.
Nên nửa đầu file là lưới an toàn cho hành vi đã có, nửa sau mới là chức năng mới.

`CouponGuardTests` là chỗ vá **lỗ hổng thật đang mở**, phát hiện khi rà lại bước 2.10:
`place_cod_order` và `vnpay_payment` đều từ chối đơn đã hủy, nhưng `checkout()` — chính
là trang áp mã — thì không. Và đơn COD đã đặt vẫn có `paid_status=False` cho tới lúc
giao hàng, nên chốt `paid_status` sẵn có cũng không chặn được nó.
"""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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


class CouponExpiryAndLimitTests(CouponTestCase):
    """Hạn dùng và số lượt — PLAN bước 2.9, SPEC-GAPS A6 (UC 3.2.21)."""

    def test_an_expired_coupon_is_rejected(self):
        self.coupon.valid_to = timezone.now() - timedelta(days=1)
        self.coupon.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))
        self.assertEqual(self.order.coupons.count(), 0)

    def test_a_coupon_expiring_later_today_still_works(self):
        """Biên: `valid_to` trong tương lai gần vẫn phải dùng được."""
        self.coupon.valid_to = timezone.now() + timedelta(hours=1)
        self.coupon.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("90000.00"))

    def test_a_coupon_without_an_expiry_never_expires(self):
        """`valid_to = None` là mặc định của mọi mã đang có trên production."""
        self.assertIsNone(self.coupon.valid_to)

        self.apply()

        self.assertEqual(self.price_of(), Decimal("90000.00"))

    def test_a_coupon_at_its_usage_limit_is_rejected(self):
        self.coupon.usage_limit = 2
        self.coupon.used_count = 2
        self.coupon.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("100000.00"))

    def test_a_coupon_with_one_use_left_still_works(self):
        self.coupon.usage_limit = 2
        self.coupon.used_count = 1
        self.coupon.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("90000.00"))

    def test_a_coupon_without_a_limit_is_never_exhausted(self):
        self.coupon.used_count = 999
        self.coupon.save()

        self.apply()

        self.assertEqual(self.price_of(), Decimal("90000.00"))

    def test_usable_error_reports_expiry_before_exhaustion(self):
        """Hết hạn VÀ hết lượt thì báo hết hạn — khách sửa được cái nào đâu, nhưng
        thông điệp phải xác định chứ không tùy thứ tự so sánh."""
        self.coupon.valid_to = timezone.now() - timedelta(days=1)
        self.coupon.usage_limit = 1
        self.coupon.used_count = 1

        self.assertEqual(self.coupon.usable_error(), Coupon.EXPIRED)

    def test_a_usable_coupon_reports_no_error(self):
        self.assertIsNone(self.coupon.usable_error())


class CouponCounterTests(CouponTestCase):
    """Bộ đếm lượt dùng — nhóm bắt lỗi thật nhất của bước 2.9.

    Bộ đếm tăng ở `CartOrder.confirm_paid()`, tức **lúc xác nhận đã thu tiền**, không
    phải lúc áp mã. Mỗi test dưới đây tương ứng với một đường có thể làm con số sai.
    """

    def place_cod(self, order=None):
        """Khách chốt đặt hàng COD.

        Phải chạy SAU khi áp mã: từ bước 2.10/commit trước, `checkout()` từ chối áp mã
        cho đơn COD đã đặt. Đây cũng chính là thứ tự thật của người dùng — áp mã ở trang
        thanh toán rồi mới bấm đặt hàng.
        """
        order = order or self.order
        self.client.post(reverse("core:place-cod-order", args=[order.oid]))

    def deliver_cod(self, order=None):
        """Nhân viên đánh dấu đơn COD đã giao — đường tăng bộ đếm của luồng COD."""
        order = order or self.order
        staff = User.objects.create_user(
            username=f"nv{order.id}", email=f"nv{order.id}@grocerly.vn",
            password="matkhau123", is_staff=True,
        )
        client = self.client_class()
        client.force_login(staff)
        for status in ('shipped', 'delivered'):
            client.post(
                reverse("useradmin:change_order_status", args=[order.oid]),
                {'status': status},
            )

    def used(self):
        self.coupon.refresh_from_db()
        return self.coupon.used_count

    def test_applying_a_coupon_does_not_increment_the_counter(self):
        """Khách áp mã rồi bỏ đi thì đơn treo mãi ở `paid_status=False`.

        Tăng bộ đếm ở lúc áp là con số phình lên vì những đơn không bao giờ thành đơn.
        """
        self.apply()

        self.assertEqual(self.used(), 0)

    def test_editing_the_cart_after_applying_a_coupon_does_not_burn_a_use(self):
        """`save_checkout_info` gọi `coupons.clear()` mỗi lần khách sửa giỏ.

        `clear()` chỉ xóa dòng M2M, nó không biết gì về bộ đếm — nên nếu bộ đếm tăng lúc
        áp mã thì khách sửa giỏ rồi áp lại là +1 lượt nữa cho **cùng một đơn**.
        """
        self.apply()
        self.order.coupons.clear()

        self.apply()

        self.assertEqual(self.used(), 0)

    def test_a_delivered_cod_order_increments_the_counter_once(self):
        """Luồng COD đầy đủ: áp mã → đặt hàng → nhân viên giao xong."""
        self.apply()
        self.place_cod()

        self.deliver_cod()

        self.assertEqual(self.used(), 1)

    def test_shipping_a_cod_order_does_not_yet_burn_a_use(self):
        """Chỉ khi GIAO XONG mới tính là đã thu tiền, không phải lúc xuất kho."""
        self.apply()
        self.place_cod()
        staff = User.objects.create_user(
            username="nv", email="nv@grocerly.vn", password="matkhau123", is_staff=True,
        )
        client = self.client_class()
        client.force_login(staff)

        client.post(
            reverse("useradmin:change_order_status", args=[self.order.oid]),
            {'status': 'shipped'},
        )

        self.assertEqual(self.used(), 0)

    def test_a_cancelled_order_never_burns_a_use(self):
        """Khách áp mã rồi hủy đơn — lượt đó không được tính."""
        self.apply()

        self.client.post(reverse("core:cancel-order", args=[self.order.oid]))

        self.assertEqual(self.used(), 0)

    def test_confirming_the_same_order_twice_increments_the_counter_once(self):
        """`confirm_paid()` phải idempotent.

        ⚠️ Test này chứng minh **tính idempotent**, KHÔNG chứng minh chống tranh chấp:
        `select_for_update()` là no-op trên SQLite, mà cả `settings_test` lẫn
        `settings_local` đều ép SQLite.
        """
        self.apply()
        self.order.refresh_from_db()

        self.assertTrue(self.order.confirm_paid())
        self.assertFalse(self.order.confirm_paid())

        self.assertEqual(self.used(), 1)

    def test_an_order_without_a_coupon_confirms_fine(self):
        self.order.refresh_from_db()

        self.assertTrue(self.order.confirm_paid())
        self.assertEqual(self.used(), 0)

    def test_two_different_orders_each_burn_a_use(self):
        self.apply()
        self.order.refresh_from_db()
        self.order.confirm_paid()

        second = self.make_order()
        self.apply(order=second)
        second.refresh_from_db()
        second.confirm_paid()

        self.assertEqual(self.used(), 2)

    def test_a_soft_deleted_coupon_still_gets_its_counter_incremented(self):
        """Quản trị viên xóa mềm mã sau khi khách đã áp — bộ đếm vẫn phải đúng.

        Chốt việc dùng `Coupon.all_objects` trong `confirm_paid()`; đổi sang `objects`
        là test này đỏ.
        """
        self.apply()
        self.coupon.soft_delete()
        self.order.refresh_from_db()

        self.order.confirm_paid()

        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.used_count, 1)

    def test_the_counter_stops_the_next_customer_once_the_limit_is_reached(self):
        """Vòng khép kín: dùng hết lượt thật rồi thì mã bị từ chối."""
        self.coupon.usage_limit = 1
        self.coupon.save()
        self.apply()
        self.order.refresh_from_db()
        self.order.confirm_paid()

        second = self.make_order()
        self.apply(order=second)

        self.assertEqual(self.price_of(second), Decimal("100000.00"))
        self.assertEqual(second.coupons.count(), 0)


class CouponDiscountBoundsTests(CouponTestCase):
    """`Coupon.discount` phải là phần trăm thật — [S-12](../../docs/SECURITY.md).

    Trường này luôn được hiểu là phần trăm nhưng trước đây không có validator nào. Quản
    trị viên gõ nhầm `1000` là `checkout()` tính `order.price -= order.price * 1000 / 100`
    và đơn hàng thành **giá âm**. Sau đó `vnpay_payment` gửi `amount = int(order.price) * 100`
    — một số âm — sang cổng thanh toán, và con số âm ấy còn chảy vào `order.saved` rồi vào
    thống kê doanh thu ở dashboard nhân viên.

    Cần quyền quản trị viên mới gây ra được, nên đây là **phòng vệ chiều sâu** chứ không
    phải lỗ hổng cho người ngoài. Nhưng nó là lỗi *gõ nhầm*, mà gõ nhầm thì rất dễ xảy ra.

    Vá ở ba mức, vì không mức nào tự đủ:

    - **Validator 1–100** chặn đường nhập liệu. `Coupon` chỉ sửa được qua Django admin
      (`CouponAdmin`), mà admin dùng ModelForm nên validator chạy thật. Nhưng validator
      **không** chạy khi gọi `objects.create()` hay `.save()`.
    - **`CHECK (discount >= 0)`** do `PositiveIntegerField` sinh ra trong migration `0010`
      chặn chiều âm ở tầng database, tức chặn mọi đường — kể cả shell và fixture.
    - **Kẹp trong `checkout()`** lo phần còn lại: cận **trên** không có ràng buộc database
      nào, và bản ghi cũ trên production ra đời trước cả hai mức trên. Giá đơn không được
      âm dù dữ liệu xấu tới đâu.
    """

    def full_clean_error_fields(self, discount):
        coupon = Coupon(code="GIAM", discount=discount, active=True)
        try:
            coupon.full_clean()
        except ValidationError as error:
            return error.message_dict
        return {}

    def test_a_discount_over_one_hundred_percent_is_rejected(self):
        self.assertIn('discount', self.full_clean_error_fields(1000))

    def test_exactly_one_hundred_percent_is_allowed(self):
        """Giảm 100% là hợp lệ — hàng tặng kèm, đơn 0 đồng."""
        self.assertNotIn('discount', self.full_clean_error_fields(100))

    def test_zero_percent_is_rejected(self):
        """Mã giảm 0% không giảm gì; nhận nó vào là bày ra một mã vô nghĩa cho khách."""
        self.assertIn('discount', self.full_clean_error_fields(0))

    def test_one_percent_is_allowed(self):
        self.assertNotIn('discount', self.full_clean_error_fields(1))

    def test_a_negative_discount_is_rejected(self):
        self.assertIn('discount', self.full_clean_error_fields(-10))

    def test_a_bad_legacy_row_cannot_drive_the_price_negative(self):
        """Đường thứ hai: bản ghi đã có trong database từ trước khi có validator.

        `Coupon.objects.create()` **không** chạy validator, nên đúng cách mà một dòng như
        thế này ra đời — và cũng đúng cách nó còn nằm đó trên production.
        """
        Coupon.objects.create(code="HONG", discount=1000, active=True)
        self.apply(code="HONG")
        self.assertGreaterEqual(self.price_of(), 0)

    def test_a_bad_legacy_row_caps_the_discount_at_the_order_total(self):
        Coupon.objects.create(code="HONG", discount=1000, active=True)
        self.apply(code="HONG")
        self.assertEqual(self.price_of(), 0)

    def test_the_database_itself_refuses_a_negative_discount(self):
        """Chiều âm được database chặn, không phải code — và đó là mức chặn mạnh nhất.

        `PositiveIntegerField` sinh ra `CHECK ("discount" >= 0)` trong migration `0010`,
        nên `objects.create(discount=-50)` **ném `IntegrityError`** chứ không lặng lẽ ghi
        vào. Nghĩa là không đường nào — shell, fixture, admin — tạo được bản ghi âm.

        Đáng chốt vì hậu quả của chiều âm khó thấy hơn chiều dương: `discount=-50` biến
        `order.price -= order.price * -50 / 100` thành phép **cộng**, tức mã "giảm giá"
        lại tăng tiền khách phải trả.

        ⚠️ Hệ quả cho lúc deploy: `CHECK` này áp lên **dữ liệu đang có**. Coupon nào trên
        Neon đang mang `discount` âm sẽ làm migration `0010` **thất bại** — phải soát
        trước, xem PLAN bước 1.1.
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Coupon.objects.create(code="AM", discount=-50, active=True)

    def test_a_normal_discount_is_untouched_by_the_cap(self):
        """Kẹp không được đụng tới đường chạy bình thường."""
        self.apply()
        self.assertEqual(self.price_of(), Decimal("90000.00"))
