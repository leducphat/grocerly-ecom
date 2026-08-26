"""Hai callback của VNPay ở mức HTTP — PLAN bước 2.9, và bịt một lỗ hổng kiểm thử.

`core/test_vnpay.py` là unit test cho **thuật toán ký** (`SimpleTestCase`, không dựng
database). File này khác: nó gọi thẳng `vnpay_return` và `vnpay_ipn` bằng test client với
query đã ký hợp lệ, tức là kiểm **luồng** chứ không kiểm hàm băm.

Vì sao cần: đường thanh toán online chính là lý do `CartOrder.confirm_paid()` tồn tại
(hai callback có thể cùng chạy cho một đơn), nhưng cho tới file này **không test nào chạm
tới hai endpoint đó**. Hệ quả đo được: gỡ cả hai lời gọi `confirm_paid()` về lại
`paid_status = True` như trước bước 2.9 thì **toàn bộ suite vẫn xanh** — nghĩa là mọi
chốt chặn của 2.9 chỉ được bảo vệ ở nhánh COD.

Chữ ký được tính lại độc lập bằng `hmac`/`hashlib`, dùng chung helper với
`core/test_vnpay.py` để hai file không lệch nhau về cách ký.
"""

from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import CartOrder, CartOrderItem, Category, Coupon, Product, Vendor
from core.test_vnpay import SECRET, expected_signature
from userauths.models import User


@override_settings(VNPAY_HASH_SECRET=SECRET)
class VnpayCallbackTestCase(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(self.customer)

        category = Category.objects.create(title="Trái cây")
        vendor = Vendor.objects.create(name="Vinamilk")
        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("100000.00"), stock_count=10,
            product_status='published', category=category, vendor=vendor,
        )
        self.order = self.make_order()
        self.coupon = Coupon.objects.create(code="GIAM10", discount=10, active=True)

    def make_order(self):
        order = CartOrder.objects.create(
            user=self.customer, price=Decimal("100000.00"), payment_method='online',
        )
        CartOrderItem.objects.create(
            order=order, product=self.product, invoice_no=f"INVOICE_NO-{order.id}",
            item=self.product.title, image="/media/products.jpg", quantity=1,
            price=self.product.price, total=self.product.price,
        )
        return order

    def callback_params(self, order=None, response_code="00"):
        """Bộ tham số VNPay trả về, đã ký hợp lệ."""
        order = order or self.order
        order.refresh_from_db()
        params = {
            'vnp_Amount': str(int(order.price) * 100),
            'vnp_BankCode': 'NCB',
            'vnp_OrderInfo': f"Thanh_toan_don_hang_{order.oid}",
            'vnp_ResponseCode': response_code,
            'vnp_TmnCode': 'GROCERLY',
            'vnp_TransactionNo': '14000000',
            'vnp_TxnRef': f"{order.oid}-1787000000",
        }
        params['vnp_SecureHash'] = expected_signature(params)
        return params

    def hand_off_to_gateway(self, order=None):
        """Bấm nút "Thanh toán qua VNPay" — POST từ 2026-08-26 (S-10)."""
        order = order or self.order
        session = self.client.session
        session['pending_order_oid'] = str(order.oid)
        session.save()
        return self.client.post(reverse("core:vnpay_payment", args=[order.oid]))

    def apply_coupon(self, order=None):
        order = order or self.order
        self.client.post(reverse("core:checkout", args=[order.oid]), {'code': "GIAM10"})

    def used(self):
        self.coupon.refresh_from_db()
        return self.coupon.used_count

    def paid(self, order=None):
        order = order or self.order
        order.refresh_from_db()
        return order.paid_status


class VnpayReturnTests(VnpayCallbackTestCase):
    """`vnpay_return` — trình duyệt khách quay về sau khi trả tiền."""

    def _call(self, order=None, response_code="00"):
        return self.client.get(
            reverse("core:vnpay_return"), self.callback_params(order, response_code)
        )

    def test_a_valid_return_marks_the_order_paid(self):
        self._call()

        self.assertTrue(self.paid())

    def test_a_valid_return_burns_one_coupon_use(self):
        """Trước file này, nhánh online không có gì chốt việc tăng bộ đếm."""
        self.apply_coupon()

        self._call()

        self.assertEqual(self.used(), 1)

    def test_a_failed_payment_marks_nothing(self):
        self.apply_coupon()

        self._call(response_code="24")   # 24 = khách hủy giao dịch ở cổng

        self.assertFalse(self.paid())
        self.assertEqual(self.used(), 0)

    def test_a_tampered_signature_marks_nothing(self):
        params = self.callback_params()
        params['vnp_Amount'] = '1'       # sửa số tiền, giữ nguyên chữ ký cũ

        self.client.get(reverse("core:vnpay_return"), params)

        self.assertFalse(self.paid())

    def test_a_cancelled_order_is_not_marked_paid(self):
        """Đơn vừa `cancelled` vừa `paid_status=True` là trạng thái không màn hình nào
        xử lý được — và nó còn đốt mất một lượt mã giảm giá."""
        self.apply_coupon()
        self.order.product_status = 'cancelled'
        self.order.save()

        self._call()

        self.assertFalse(self.paid())
        self.assertEqual(self.used(), 0)


class VnpayIpnTests(VnpayCallbackTestCase):
    """`vnpay_ipn` — VNPay gọi thẳng vào server, không qua trình duyệt khách."""

    def _call(self, order=None, response_code="00"):
        return self.client.get(
            reverse("core:vnpay_ipn"), self.callback_params(order, response_code)
        )

    def test_a_valid_ipn_confirms_the_order(self):
        response = self._call()

        self.assertEqual(response.json()['RspCode'], '00')
        self.assertTrue(self.paid())

    def test_a_valid_ipn_burns_one_coupon_use(self):
        self.apply_coupon()

        self._call()

        self.assertEqual(self.used(), 1)

    def test_a_repeated_ipn_does_not_burn_a_second_use(self):
        """VNPay gọi lại IPN cho tới khi nhận được phản hồi — nên nó gọi nhiều lần là
        chuyện bình thường, không phải bất thường."""
        self.apply_coupon()
        self._call()

        response = self._call()

        self.assertEqual(response.json()['RspCode'], '02')
        self.assertEqual(self.used(), 1)

    def test_a_cancelled_order_is_refused(self):
        self.apply_coupon()
        self.order.product_status = 'cancelled'
        self.order.save()

        response = self._call()

        self.assertEqual(response.json()['RspCode'], '02')
        self.assertFalse(self.paid())
        self.assertEqual(self.used(), 0)

    def test_a_tampered_signature_is_refused(self):
        params = self.callback_params()
        params['vnp_Amount'] = '1'

        response = self.client.get(reverse("core:vnpay_ipn"), params)

        self.assertEqual(response.json()['RspCode'], '97')
        self.assertFalse(self.paid())


class VnpayAndReturnTogetherTests(VnpayCallbackTestCase):
    """Hai callback cùng chạy cho một đơn — chính là lý do `confirm_paid()` tồn tại."""

    def test_the_ipn_and_the_return_together_burn_only_one_use(self):
        """Trước bước 2.9, `vnpay_ipn` có chốt `if order.paid_status` còn `vnpay_return`
        thì **không**, nên hai đường cùng chạy là cộng đôi.
        """
        self.apply_coupon()
        params = self.callback_params()

        self.client.get(reverse("core:vnpay_ipn"), params)
        self.client.get(reverse("core:vnpay_return"), params)

        self.assertEqual(self.used(), 1)
        self.assertTrue(self.paid())

    def test_the_usage_limit_holds_across_the_online_path(self):
        """Vòng khép kín: hết lượt thật rồi thì khách sau bị chặn."""
        self.coupon.usage_limit = 1
        self.coupon.save()
        self.apply_coupon()
        self.client.get(reverse("core:vnpay_return"), self.callback_params())

        second = self.make_order()
        self.apply_coupon(second)

        second.refresh_from_db()
        self.assertEqual(second.price, Decimal("100000.00"))
        self.assertEqual(second.coupons.count(), 0)


class AmountLockedAtHandoffTests(VnpayCallbackTestCase):
    """Số tiền được chốt lúc chuyển sang cổng — [S-13](../../docs/SECURITY.md), [ADR-0008](../../docs/DECISIONS.md).

    `vnpay_payment` chốt `amount = int(order.price) * 100` **tại thời điểm chuyển hướng**,
    còn `vnpay_ipn` trước đây lại đối chiếu với `order.price` **đang có trong database lúc
    nhận callback**. Hai con số đó có thể khác nhau, và khi khác thì IPN trả `'04'` —
    nghĩa là **khách mất tiền thật mà đơn không bao giờ được ghi nhận đã thanh toán**, và
    `used_count` của mã giảm giá cũng không tăng.

    Đường đi tới chỗ lệch: mở `/checkout/<oid>/` ở tab khác rồi áp thêm mã giảm giá sau
    khi đã bấm sang VNPay. Bản vá bước 2.9/2.10 đã bịt đường tương tự cho đơn COD
    (`checkout()` từ chối đơn `payment_method == 'cod'`), nhưng đơn online sang cổng rồi
    thì `payment_method` vẫn là `'online'` nên không có gì chặn.
    """

    def test_handoff_records_the_amount_that_was_sent(self):
        self.hand_off_to_gateway()
        self.order.refresh_from_db()
        self.assertEqual(self.order.vnpay_amount, int(Decimal("100000.00")) * 100)

    def test_the_checkout_page_refuses_a_coupon_after_handoff(self):
        """Khóa giá sau khi đã sang cổng — nửa còn lại của bản vá.

        Chỉ so theo số tiền đã gửi thì đơn vẫn được ghi nhận đã trả, nhưng `order.price`
        lại nói một con số khác với số khách thật sự trả. Khóa luôn là cách duy nhất giữ
        hai con số bằng nhau.
        """
        self.hand_off_to_gateway()
        self.apply_coupon()
        self.order.refresh_from_db()
        self.assertEqual(self.order.price, Decimal("100000.00"))
        self.assertEqual(self.used(), 0)

    def test_the_ipn_still_confirms_after_a_price_change(self):
        """Kịch bản đầy đủ của S-13, đi qua đúng thứ tự khách hàng gặp."""
        self.hand_off_to_gateway()
        params = self.callback_params()

        # Giả lập giá bị đổi sau khi đã sang cổng — nay `checkout()` chặn đường này, nên
        # ghi thẳng vào database để test vẫn tái hiện được tình huống.
        self.order.price = Decimal("90000.00")
        self.order.save(update_fields=['price'])

        response = self.client.get(reverse("core:vnpay_ipn"), params)
        self.assertEqual(response.json()['RspCode'], '00')
        self.assertTrue(self.paid())

    def test_the_ipn_still_rejects_an_amount_that_was_never_sent(self):
        """Khóa chặt hơn chứ không lỏng hơn: chốt chống giả mạo số tiền vẫn còn."""
        self.hand_off_to_gateway()
        params = self.callback_params()
        params['vnp_Amount'] = str(int(Decimal("1.00")) * 100)
        params['vnp_SecureHash'] = expected_signature(
            {k: v for k, v in params.items() if k != 'vnp_SecureHash'}
        )

        response = self.client.get(reverse("core:vnpay_ipn"), params)
        self.assertEqual(response.json()['RspCode'], '04')
        self.assertFalse(self.paid())

    def test_an_order_that_never_reached_the_gateway_falls_back_to_its_price(self):
        """Đơn có từ trước migration `0011` mang `vnpay_amount = NULL`.

        Chúng vẫn phải thanh toán được, nên nhánh dự phòng đọc `order.price` — đúng hành
        vi cũ. Không có nhánh này là mọi đơn treo trên production hỏng ngay sau khi deploy.
        """
        self.order.refresh_from_db()
        self.assertIsNone(self.order.vnpay_amount)

        response = self.client.get(reverse("core:vnpay_ipn"), self.callback_params())
        self.assertEqual(response.json()['RspCode'], '00')
        self.assertTrue(self.paid())

    def test_a_coupon_applied_before_handoff_is_what_gets_sent(self):
        """Khóa chỉ áp dụng **sau** khi sang cổng — áp mã trước đó vẫn bình thường."""
        self.apply_coupon()
        self.hand_off_to_gateway()
        self.order.refresh_from_db()
        self.assertEqual(self.order.price, Decimal("90000.00"))
        self.assertEqual(self.order.vnpay_amount, 90000 * 100)

    def test_going_back_to_the_gateway_restamps_the_amount(self):
        """Khách bỏ dở rồi quay lại bấm trả tiếp: lần chuyển hướng sau ghi đè lần trước.

        Quan trọng vì con số cũ mà còn lại thì lần trả sau bị từ chối — đúng lỗi mà bản
        vá này đang sửa, chỉ khác hình dạng.
        """
        self.hand_off_to_gateway()
        self.order.price = Decimal("80000.00")
        self.order.save(update_fields=['price'])
        self.hand_off_to_gateway()
        self.order.refresh_from_db()
        self.assertEqual(self.order.vnpay_amount, 80000 * 100)
