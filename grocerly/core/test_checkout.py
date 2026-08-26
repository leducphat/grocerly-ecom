"""Luồng tạo đơn — PLAN bước 2.6f.

`save_checkout_info` là chỗ giỏ hàng trong session biến thành `CartOrder` +
`CartOrderItem`. [ADR-0005](../../docs/DECISIONS.md) gọi đây là *"luồng rủi ro nhất"*,
và cho tới file này nó **không có một test nào** — trong khi bước 2.11 sắp viết lại đúng
hàm này để thêm khóa ngoại `Product` cho `CartOrderItem`.

Mục đích của file: **chốt hành vi đang có** trước khi thay đổi, để 2.11 làm gì lệch là
thấy ngay. Nhóm `CartOrderItemSnapshotTests` là nhóm 2.11 sẽ động vào — mỗi test ở đó
ghi rõ cái gì phải giữ nguyên và cái gì được phép đổi.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, CartOrderItem, Category, Coupon, Product, Vendor
from userauths.models import User


CHECKOUT_FORM = {
    'full_name': "Lê Văn A",
    'email': "levana@example.com",
    'mobile': "0900000000",
    'address': "12 Võ Văn Ngân",
    'city': "Thủ Đức",
    'state': "TP.HCM",
    'country': "Việt Nam",
}


class CheckoutTestCase(TestCase):
    """Nền chung: một khách đã đăng nhập và hai sản phẩm đang bán."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(self.user)

        # Sản phẩm phải có đủ `category` và `vendor`: thiếu một trong hai là trang chủ
        # ném NoReverseMatch khi `assertRedirects` đi theo redirect. Đó là lỗi riêng,
        # không phải chuyện của checkout — xem `core/test_missing_relations.py`.
        self.category = Category.objects.create(title="Trái cây")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        common = dict(
            stock_count=10, product_status='published',
            category=self.category, vendor=self.vendor,
        )
        self.watermelon = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), **common
        )
        self.mango = Product.objects.create(
            title="Xoài cát", price=Decimal("70000.00"), **common
        )

    def add_to_cart(self, product, qty=1):
        response = self.client.get(
            reverse("core:add-to-cart"), {'id': product.id, 'qty': qty}
        )
        self.assertEqual(response.status_code, 200)

    def save_checkout(self, **overrides):
        data = dict(CHECKOUT_FORM)
        data.update(overrides)
        return self.client.post(reverse("core:save_checkout_info"), data)


class SaveCheckoutInfoTests(CheckoutTestCase):
    """Đường đi thuận: giỏ hàng thành đơn hàng."""

    def test_an_order_is_created_for_the_signed_in_customer(self):
        self.add_to_cart(self.watermelon, qty=2)

        self.save_checkout()

        order = CartOrder.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.full_name, "Lê Văn A")
        self.assertEqual(order.address, "12 Võ Văn Ngân")

    def test_the_order_total_is_the_sum_of_the_cart_lines(self):
        self.add_to_cart(self.watermelon, qty=2)   # 100.000
        self.add_to_cart(self.mango, qty=1)        #  70.000

        self.save_checkout()

        self.assertEqual(CartOrder.objects.get().price, Decimal("170000.00"))

    def test_one_order_item_per_cart_line(self):
        self.add_to_cart(self.watermelon, qty=2)
        self.add_to_cart(self.mango, qty=1)

        self.save_checkout()

        items = CartOrderItem.objects.order_by('item')
        self.assertEqual([i.item for i in items], ["Dưa hấu", "Xoài cát"])
        self.assertEqual([i.quantity for i in items], [2, 1])

    def test_the_line_total_is_quantity_times_price(self):
        self.add_to_cart(self.watermelon, qty=3)

        self.save_checkout()

        item = CartOrderItem.objects.get()
        self.assertEqual(item.price, Decimal("50000.00"))
        self.assertEqual(item.total, Decimal("150000.00"))

    def test_every_line_shares_one_invoice_number(self):
        self.add_to_cart(self.watermelon)
        self.add_to_cart(self.mango)

        self.save_checkout()

        order = CartOrder.objects.get()
        numbers = {i.invoice_no for i in CartOrderItem.objects.all()}
        self.assertEqual(numbers, {f"INVOICE_NO-{order.id}"})

    def test_the_customer_lands_on_the_checkout_page_for_the_new_order(self):
        self.add_to_cart(self.watermelon)

        response = self.save_checkout()

        order = CartOrder.objects.get()
        self.assertRedirects(response, reverse("core:checkout", args=[order.oid]))

    def test_the_order_is_remembered_in_the_session(self):
        """`pending_order_oid` là thứ cho khách quay lại hoàn tất đơn chưa trả tiền."""
        self.add_to_cart(self.watermelon)

        self.save_checkout()

        order = CartOrder.objects.get()
        self.assertEqual(self.client.session['pending_order_oid'], str(order.oid))

    def test_the_cart_is_not_emptied_yet(self):
        """Giỏ chỉ được xóa khi thanh toán xong, không phải lúc tạo đơn."""
        self.add_to_cart(self.watermelon)

        self.save_checkout()

        self.assertIn('cart_data_obj', self.client.session)


class CartOrderItemSnapshotTests(CheckoutTestCase):
    """⚠️ Nhóm này là thứ **PLAN bước 2.11 sẽ động vào** — [ADR-0006](../../docs/DECISIONS.md).

    `CartOrderItem` hiện lưu **bản sao tĩnh** của sản phẩm (`item`, `image`, `price`) và
    **không có khóa ngoại** tới `Product`. Bản sao tĩnh là thiết kế có chủ ý và **phải
    giữ nguyên** sau 2.11: hóa đơn của khách không được đổi khi sản phẩm bị sửa hay xóa.

    Cái 2.11 thêm vào là một khóa ngoại **song song** với bản sao đó. Nên:

    - `test_the_snapshot_survives_*` : phải **vẫn xanh** sau 2.11
    - `test_there_is_no_link_back_*` : phải **đổi kỳ vọng** sau 2.11 — đó chính là mục tiêu
    """

    def test_the_snapshot_survives_a_price_change(self):
        self.add_to_cart(self.watermelon, qty=2)
        self.save_checkout()

        self.watermelon.price = Decimal("999000.00")
        self.watermelon.save()

        item = CartOrderItem.objects.get()
        self.assertEqual(item.price, Decimal("50000.00"))
        self.assertEqual(item.total, Decimal("100000.00"))
        self.assertEqual(CartOrder.objects.get().price, Decimal("100000.00"))

    def test_the_snapshot_survives_a_rename(self):
        self.add_to_cart(self.watermelon)
        self.save_checkout()

        self.watermelon.title = "Dưa hấu không hạt"
        self.watermelon.save()

        self.assertEqual(CartOrderItem.objects.get().item, "Dưa hấu")

    def test_the_snapshot_survives_the_product_being_deleted(self):
        self.add_to_cart(self.watermelon)
        self.save_checkout()

        self.watermelon.hard_delete()

        item = CartOrderItem.objects.get()
        self.assertEqual(item.item, "Dưa hấu")
        self.assertEqual(item.price, Decimal("50000.00"))

    def test_there_is_no_link_back_to_the_product(self):
        """Chốt tình trạng HIỆN TẠI. Sau bước 2.11 test này phải đổi.

        Không có khóa ngoại nghĩa là câu *"người này đã mua sản phẩm kia chưa"* chỉ trả
        lời được bằng cách so tên — nguồn gốc của nợ kỹ thuật #6 và lý do A2 chưa cài.
        """
        self.add_to_cart(self.watermelon)
        self.save_checkout()

        field_names = {f.name for f in CartOrderItem._meta.get_fields()}
        self.assertNotIn('product', field_names)

    def test_matching_by_name_is_ambiguous_when_two_products_share_a_title(self):
        """Vì sao khớp theo tên là không đủ — bước 2.11 xóa hẳn vấn đề này."""
        twin = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), stock_count=10,
            product_status='published', category=self.category, vendor=self.vendor,
        )
        self.add_to_cart(self.watermelon)
        self.save_checkout()

        matches = Product.objects.filter(title=CartOrderItem.objects.get().item)
        self.assertEqual(matches.count(), 2)
        self.assertIn(twin, matches)

    def test_the_price_comes_from_the_cart_not_from_the_product_row(self):
        """Giá chốt tại thời điểm **thêm vào giỏ**, không phải lúc bấm đặt hàng.

        Sau bản vá S-02 giá vào giỏ được đọc từ database, nên đây không phải lỗ hổng —
        nhưng nó là một quyết định nghiệp vụ chưa ai ghi lại: sản phẩm lên giá giữa lúc
        khách bỏ vào giỏ và lúc thanh toán thì khách trả giá cũ.
        """
        self.add_to_cart(self.watermelon, qty=1)

        self.watermelon.price = Decimal("80000.00")
        self.watermelon.save()

        self.save_checkout()

        self.assertEqual(CartOrder.objects.get().price, Decimal("50000.00"))


class PendingOrderReuseTests(CheckoutTestCase):
    """Quay lại bước nhập thông tin không được sinh đơn trùng."""

    def test_a_second_submission_reuses_the_same_order(self):
        self.add_to_cart(self.watermelon)
        self.save_checkout()

        self.save_checkout(full_name="Lê Văn B")

        self.assertEqual(CartOrder.objects.count(), 1)
        self.assertEqual(CartOrder.objects.get().full_name, "Lê Văn B")

    def test_the_old_lines_are_replaced_not_appended(self):
        self.add_to_cart(self.watermelon)
        self.save_checkout()
        self.assertEqual(CartOrderItem.objects.count(), 1)

        self.add_to_cart(self.mango)
        self.save_checkout()

        self.assertEqual(CartOrderItem.objects.count(), 2)
        self.assertEqual(
            sorted(i.item for i in CartOrderItem.objects.all()),
            ["Dưa hấu", "Xoài cát"],
        )

    def test_the_total_is_recalculated_from_the_new_cart(self):
        self.add_to_cart(self.watermelon, qty=1)
        self.save_checkout()

        self.add_to_cart(self.mango, qty=1)
        self.save_checkout()

        self.assertEqual(CartOrder.objects.get().price, Decimal("120000.00"))

    def test_an_applied_coupon_is_dropped_when_the_cart_changes(self):
        """Không bỏ thì khách giữ được phần giảm giá của một giỏ hàng đã khác."""
        self.add_to_cart(self.watermelon, qty=2)
        self.save_checkout()

        coupon = Coupon.objects.create(code="GIAM10", discount=10, active=True)
        order = CartOrder.objects.get()
        order.coupons.add(coupon)
        order.saved = Decimal("10000.00")
        order.save()

        self.save_checkout()

        order.refresh_from_db()
        self.assertEqual(order.coupons.count(), 0)
        self.assertEqual(order.saved, Decimal("0.00"))
        self.assertEqual(order.price, Decimal("100000.00"))

    def test_a_paid_order_is_never_reused(self):
        """Đơn đã trả tiền phải sinh đơn mới, không được ghi đè lên."""
        self.add_to_cart(self.watermelon)
        self.save_checkout()

        paid = CartOrder.objects.get()
        paid.paid_status = True
        paid.save()

        self.save_checkout()

        self.assertEqual(CartOrder.objects.count(), 2)
        paid.refresh_from_db()
        self.assertTrue(paid.paid_status)

    def test_another_customers_order_is_never_reused(self):
        """`pending_order_oid` đến từ session nên phải kiểm cả chủ sở hữu."""
        other = User.objects.create_user(
            username="nguoikhac", email="nguoikhac@example.com", password="matkhau123",
        )
        foreign = CartOrder.objects.create(user=other, price=Decimal("1.00"))

        self.add_to_cart(self.watermelon)
        session = self.client.session
        session['pending_order_oid'] = str(foreign.oid)
        session.save()

        self.save_checkout()

        foreign.refresh_from_db()
        self.assertEqual(foreign.price, Decimal("1.00"))
        self.assertEqual(CartOrder.objects.filter(user=self.user).count(), 1)


class SaveCheckoutInfoGuardTests(CheckoutTestCase):
    """Đầu vào thiếu hoặc sai bối cảnh thì không được tạo đơn."""

    def test_a_missing_name_creates_nothing(self):
        self.add_to_cart(self.watermelon)

        response = self.save_checkout(full_name="")

        self.assertEqual(CartOrder.objects.count(), 0)
        self.assertRedirects(response, reverse("core:checkout-info"))

    def test_a_missing_email_creates_nothing(self):
        self.add_to_cart(self.watermelon)

        self.save_checkout(email="")

        self.assertEqual(CartOrder.objects.count(), 0)

    def test_a_missing_address_creates_nothing(self):
        self.add_to_cart(self.watermelon)

        self.save_checkout(address="")

        self.assertEqual(CartOrder.objects.count(), 0)

    def test_an_empty_cart_creates_nothing(self):
        response = self.save_checkout()

        self.assertEqual(CartOrder.objects.count(), 0)
        self.assertRedirects(response, reverse("core:index"))

    def test_a_get_creates_nothing(self):
        self.add_to_cart(self.watermelon)

        response = self.client.get(reverse("core:save_checkout_info"))

        self.assertEqual(CartOrder.objects.count(), 0)
        self.assertRedirects(response, reverse("core:index"))

    def test_a_guest_cannot_place_an_order(self):
        self.add_to_cart(self.watermelon)
        self.client.logout()

        response = self.save_checkout()

        self.assertEqual(CartOrder.objects.count(), 0)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("userauths:sign-in"), response.url)
