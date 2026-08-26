"""Khách tự hủy đơn — PLAN bước 2.10, SPEC-GAPS A7 (UC 3.2.25).

`STATUS_CHOICES` trước đây chỉ có `processing`/`shipped`/`delivered`, nên use case "Hủy
đơn" trong báo cáo không có gì để demo. Nay thêm `cancelled` và **đó là trạng thái cuối**.

Hai giới hạn của việc hủy đều có lý do kỹ thuật, không phải quy tắc tùy tiện:

- **Chỉ hủy đơn còn `processing`.** Tồn kho chỉ bị trừ lúc đơn chuyển sang `shipped`
  (`change_order_status`), nên hủy trước mốc đó **không cần hoàn kho**. Nhánh hoàn kho
  không tồn tại thì không thể viết sai — nhóm `CancelDoesNotTouchStockTests` chốt lại
  điều đó.
- **Chỉ hủy đơn chưa thanh toán.** Hủy đơn đã trả tiền nghĩa là phải hoàn tiền, mà VNPay
  ở đây chỉ tích hợp chiều thu. Cho bấm Hủy ở đó là hứa một thứ không tồn tại.

Nhóm `CancelledOrderStaysCancelledTests` là phần dễ sót nhất: **hai** đường thanh toán
đều gán thẳng `product_status = 'processing'`, nên thiếu chốt là mở lại URL thanh toán
sẽ hồi sinh một đơn đã hủy.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, CartOrderItem, Category, Product, Vendor
from userauths.models import User


class CancelOrderTestCase(TestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(self.customer)

        self.category = Category.objects.create(title="Trái cây")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), stock_count=10,
            product_status='published', category=self.category, vendor=self.vendor,
        )
        self.order = self.make_order()

    def make_order(self, user=None, status='processing', paid=False):
        order = CartOrder.objects.create(
            user=user or self.customer,
            price=self.product.price,
            product_status=status,
            paid_status=paid,
            payment_method='cod',
        )
        CartOrderItem.objects.create(
            order=order,
            product=self.product,
            invoice_no=f"INVOICE_NO-{order.id}",
            item=self.product.title,
            image="/media/products.jpg",
            quantity=2,
            price=self.product.price,
            total=self.product.price * 2,
        )
        return order

    def cancel(self, order=None):
        order = order or self.order
        return self.client.post(reverse("core:cancel-order", args=[order.oid]))

    def status_of(self, order=None):
        order = order or self.order
        order.refresh_from_db()
        return order.product_status


class WhenAnOrderMayBeCancelledTests(CancelOrderTestCase):

    def test_a_processing_order_can_be_cancelled(self):
        response = self.cancel()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.status_of(), 'cancelled')

    def test_a_shipped_order_cannot_be_cancelled(self):
        """Hàng đã rời kho — và tồn kho đã bị trừ."""
        order = self.make_order(status='shipped')

        self.cancel(order)

        self.assertEqual(self.status_of(order), 'shipped')

    def test_a_delivered_order_cannot_be_cancelled(self):
        order = self.make_order(status='delivered')

        self.cancel(order)

        self.assertEqual(self.status_of(order), 'delivered')

    def test_a_paid_order_cannot_be_cancelled(self):
        """Không có luồng hoàn tiền, nên không hứa hủy đơn đã trả tiền."""
        order = self.make_order(status='processing', paid=True)

        self.cancel(order)

        self.assertEqual(self.status_of(order), 'processing')

    def test_an_unpaid_cod_order_can_be_cancelled(self):
        """`paid_status` của COD chỉ bật khi giao tới tay khách, nên đơn COD đang xử lý
        vẫn thỏa cả hai điều kiện — đây là trường hợp phổ biến nhất."""
        self.assertFalse(self.order.paid_status)

        self.cancel()

        self.assertEqual(self.status_of(), 'cancelled')

    def test_cancelling_twice_changes_nothing(self):
        self.cancel()

        response = self.cancel()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.status_of(), 'cancelled')


class CancelDoesNotTouchStockTests(CancelOrderTestCase):
    """Hủy **không** đụng tồn kho, và đó là hệ quả của việc chỉ cho hủy trước `shipped`."""

    def test_cancelling_leaves_stock_alone(self):
        self.cancel()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_count, 10)

    def test_the_invoice_lines_are_kept(self):
        """Hủy đơn không phải xóa đơn — bản ghi vẫn còn để tra cứu."""
        self.cancel()

        self.assertEqual(CartOrderItem.objects.filter(order=self.order).count(), 1)
        self.assertTrue(CartOrder.objects.filter(pk=self.order.pk).exists())


class CancelledOrderStaysCancelledTests(CancelOrderTestCase):
    """Không đường nào được hồi sinh một đơn đã hủy.

    Cả `place_cod_order` lẫn `vnpay_payment` đều gán thẳng
    `product_status = 'processing'` — thiếu chốt chặn là mở lại URL thanh toán sẽ lật
    ngược trạng thái.
    """

    def test_placing_a_cod_order_again_does_not_revive_it(self):
        self.cancel()

        response = self.client.post(
            reverse("core:place-cod-order", args=[self.order.oid])
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.status_of(), 'cancelled')
        self.assertFalse(CartOrder.objects.get(pk=self.order.pk).paid_status)

    def test_starting_a_vnpay_payment_does_not_revive_it(self):
        self.cancel()

        self.client.get(reverse("core:vnpay_payment", args=[self.order.oid]))

        self.assertEqual(self.status_of(), 'cancelled')

    def _checkout(self):
        self.client.get(
            reverse("core:add-to-cart"), {'id': self.product.id, 'qty': 1}
        )
        return self.client.post(reverse("core:save_checkout_info"), {
            'full_name': "Lê Văn A", 'email': "a@example.com", 'mobile': "0900000000",
            'address': "12 Võ Văn Ngân", 'city': "Thủ Đức", 'state': "TP.HCM",
            'country': "Việt Nam",
        })

    def test_checkout_does_not_reuse_an_order_cancelled_by_staff(self):
        """Kịch bản thật của chốt chặn trong `_get_pending_order_from_session`.

        Khách tự hủy thì `cancel_order` đã xóa `pending_order_oid` khỏi session, nên
        đường đó không chạm tới chốt này. Chỗ chạm tới là khi **nhân viên** hủy đơn: khách
        không đụng gì vào session của mình, `pending_order_oid` vẫn trỏ tới đơn đã hủy, và
        lần thanh toán sau sẽ tái sử dụng đúng đơn đó nếu không lọc.
        """
        session = self.client.session
        session['pending_order_oid'] = str(self.order.oid)
        session.save()
        # Nhân viên hủy — không qua view của khách, nên session của khách còn nguyên.
        CartOrder.objects.filter(pk=self.order.pk).update(product_status='cancelled')

        self._checkout()

        self.assertEqual(self.status_of(), 'cancelled')
        self.assertEqual(CartOrder.objects.count(), 2)

    def test_checkout_after_cancelling_creates_a_new_order(self):
        """Khách hủy rồi đặt lại phải ra đơn MỚI, không phải đơn vừa hủy."""
        session = self.client.session
        session['pending_order_oid'] = str(self.order.oid)
        session.save()
        self.cancel()

        self._checkout()

        self.assertEqual(self.status_of(), 'cancelled')
        self.assertEqual(CartOrder.objects.count(), 2)

    def test_the_pending_order_is_forgotten_from_the_session(self):
        session = self.client.session
        session['pending_order_oid'] = str(self.order.oid)
        session.save()

        self.cancel()

        self.assertNotIn('pending_order_oid', self.client.session)

    def test_cancelling_a_different_order_leaves_the_session_alone(self):
        other = self.make_order()
        session = self.client.session
        session['pending_order_oid'] = str(other.oid)
        session.save()

        self.cancel()

        self.assertEqual(self.client.session['pending_order_oid'], str(other.oid))


class CancelPermissionTests(CancelOrderTestCase):

    def test_another_customer_cannot_cancel_this_order(self):
        stranger = User.objects.create_user(
            username="nguoila", email="nguoila@example.com", password="matkhau123",
        )
        self.client.force_login(stranger)

        response = self.cancel()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.status_of(), 'processing')

    def test_an_anonymous_visitor_is_sent_to_login(self):
        self.client.logout()

        response = self.cancel()

        self.assertEqual(response.status_code, 302)
        self.assertIn("/sign-in", response.url)
        self.assertEqual(self.status_of(), 'processing')

    def test_a_get_request_cancels_nothing(self):
        """Thao tác đổi dữ liệu phải là POST — cùng lý do đã đưa `delete_product` sang POST."""
        response = self.client.get(reverse("core:cancel-order", args=[self.order.oid]))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.status_of(), 'processing')

    def test_a_post_without_a_csrf_token_cancels_nothing(self):
        csrf_client = self.client_class(enforce_csrf_checks=True)
        csrf_client.force_login(self.customer)

        response = csrf_client.post(reverse("core:cancel-order", args=[self.order.oid]))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.status_of(), 'processing')

    def test_an_unknown_order_returns_404_instead_of_crashing(self):
        response = self.client.post(reverse("core:cancel-order", args=["khong-co-that"]))

        self.assertEqual(response.status_code, 404)


class CancelButtonTests(CancelOrderTestCase):
    """Nút Hủy ở trang chi tiết đơn của khách."""

    def _page(self, order=None):
        order = order or self.order
        return self.client.get(reverse("core:order-detail", args=[order.id]))

    def test_the_button_is_offered_for_a_processing_order(self):
        self.assertContains(self._page(), "Cancel this order")

    def test_the_button_is_hidden_once_the_order_ships(self):
        order = self.make_order(status='shipped')

        self.assertNotContains(self._page(order), "Cancel this order")

    def test_the_button_is_hidden_for_a_paid_order(self):
        order = self.make_order(status='processing', paid=True)

        self.assertNotContains(self._page(order), "Cancel this order")

    def test_the_button_is_gone_after_cancelling(self):
        self.cancel()

        self.assertNotContains(self._page(), "Cancel this order")

    def test_the_page_posts_the_cancel_with_a_csrf_token(self):
        response = self._page()

        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, reverse("core:cancel-order", args=[self.order.oid]))

    def test_the_button_asks_for_confirmation(self):
        self.assertContains(self._page(), "confirm(")

    def test_the_page_shows_the_order_status(self):
        self.cancel()

        self.assertContains(self._page(), "Cancelled")

    def test_another_customers_order_is_not_viewable(self):
        stranger = User.objects.create_user(
            username="nguoila", email="nguoila@example.com", password="matkhau123",
        )
        self.client.force_login(stranger)

        self.assertEqual(self._page().status_code, 404)
