"""Nhập mã vận đơn ở trang nhân viên — PLAN bước 2.7, SPEC-GAPS A9 (UC 3.2.20 Alternate Flow).

Trường `tracking_id` **đã có trong model từ migration đầu tiên** nhưng chưa bao giờ có ô
nhập ở giao diện nhân viên: muốn sửa phải vào trang Django Admin. Đây là mục hiếm trong
nhóm A mà báo cáo mô tả đúng còn code thiếu, nên chỉ phải bù giao diện chứ không phải
đụng cơ sở dữ liệu.

Mã vận đơn để ở **form riêng**, không gộp vào form đổi trạng thái: hai thao tác độc lập,
gộp lại thì sửa mã là đơn nhảy trạng thái theo.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder
from userauths.models import User


class TrackingIdTestCase(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username="nhanvien", email="nhanvien@grocerly.vn", password="matkhau123",
            is_staff=True,
        )
        self.client.force_login(self.staff)
        self.order = CartOrder.objects.create(
            user=self.staff, price=Decimal("50000.00"), product_status='processing',
        )

    def save_tracking(self, value, order=None):
        order = order or self.order
        return self.client.post(
            reverse("useradmin:update_tracking_id", args=[order.oid]),
            {'tracking_id': value},
        )

    def tracking_of(self, order=None):
        order = order or self.order
        order.refresh_from_db()
        return order.tracking_id

    def page(self, order=None):
        order = order or self.order
        return self.client.get(reverse("useradmin:order_detail", args=[order.id]))


class SavingATrackingNumberTests(TrackingIdTestCase):

    def test_staff_can_save_a_tracking_number(self):
        response = self.save_tracking("GHN123456789")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.tracking_of(), "GHN123456789")

    def test_an_existing_number_can_be_replaced(self):
        self.save_tracking("GHN111")

        self.save_tracking("GHN222")

        self.assertEqual(self.tracking_of(), "GHN222")

    def test_surrounding_whitespace_is_trimmed(self):
        """Dán mã từ email của hãng vận chuyển hay kèm khoảng trắng."""
        self.save_tracking("  GHN123456789  ")

        self.assertEqual(self.tracking_of(), "GHN123456789")

    def test_an_empty_value_clears_the_number_to_null(self):
        """Lưu `None` chứ không phải chuỗi rỗng, để trang của khách chỉ phải kiểm một
        trường hợp "chưa có mã" thay vì hai."""
        self.save_tracking("GHN123456789")

        self.save_tracking("")

        self.assertIsNone(self.tracking_of())

    def test_a_whitespace_only_value_also_clears_it(self):
        self.save_tracking("GHN123456789")

        self.save_tracking("   ")

        self.assertIsNone(self.tracking_of())

    def test_saving_a_tracking_number_does_not_change_the_order_status(self):
        """Hai thao tác độc lập — đây là lý do dùng form riêng."""
        self.save_tracking("GHN123456789")

        self.order.refresh_from_db()
        self.assertEqual(self.order.product_status, 'processing')

    def test_a_shipped_order_can_still_get_its_number(self):
        """Thực tế mã vận đơn thường có ĐÚNG LÚC chuyển sang đã giao vận."""
        self.order.product_status = 'shipped'
        self.order.save()

        self.save_tracking("GHN123456789")

        self.assertEqual(self.tracking_of(), "GHN123456789")

    def test_a_cancelled_order_has_no_shipment_to_track(self):
        self.order.product_status = 'cancelled'
        self.order.save()

        self.save_tracking("GHN123456789")

        self.assertIsNone(self.tracking_of())


class TrackingPermissionTests(TrackingIdTestCase):

    def test_a_customer_cannot_set_a_tracking_number(self):
        self.client.logout()
        khach = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(khach)

        self.save_tracking("GHN123456789")

        self.assertIsNone(self.tracking_of())

    def test_a_get_request_changes_nothing(self):
        response = self.client.get(
            reverse("useradmin:update_tracking_id", args=[self.order.oid])
        )

        self.assertEqual(response.status_code, 405)
        self.assertIsNone(self.tracking_of())

    def test_a_post_without_a_csrf_token_changes_nothing(self):
        csrf_client = self.client_class(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)

        response = csrf_client.post(
            reverse("useradmin:update_tracking_id", args=[self.order.oid]),
            {'tracking_id': "GHN123456789"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertIsNone(self.tracking_of())

    def test_an_unknown_order_returns_404_instead_of_crashing(self):
        response = self.client.post(
            reverse("useradmin:update_tracking_id", args=["khong-co-that"]),
            {'tracking_id': "GHN123456789"},
        )

        self.assertEqual(response.status_code, 404)


class TrackingFormTests(TrackingIdTestCase):
    """Ô nhập ở trang chi tiết đơn của nhân viên."""

    def test_the_form_is_offered(self):
        response = self.page()

        self.assertContains(response, 'name="tracking_id"')
        self.assertContains(
            response, reverse("useradmin:update_tracking_id", args=[self.order.oid])
        )

    def test_the_current_number_is_prefilled(self):
        self.save_tracking("GHN123456789")

        self.assertContains(self.page(), 'value="GHN123456789"')

    def test_an_empty_number_renders_as_an_empty_field_not_the_word_none(self):
        """`tracking_id` là `NULL`, và `{{ None }}` render ra chuỗi "None"."""
        response = self.page()

        self.assertContains(response, 'value=""')
        self.assertNotContains(response, 'value="None"')

    def test_the_form_is_disabled_for_a_cancelled_order(self):
        self.order.product_status = 'cancelled'
        self.order.save()

        response = self.page()

        self.assertContains(response, "no shipment to track")


class CustomerSeesTrackingTests(TestCase):
    """Mã vận đơn phải hiện ở trang đơn hàng của khách — nhập vào mà khách không thấy
    thì chức năng chưa hoàn chỉnh."""

    def setUp(self):
        self.customer = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(self.customer)
        self.order = CartOrder.objects.create(
            user=self.customer, price=Decimal("50000.00"), product_status='shipped',
        )

    def _page(self):
        return self.client.get(reverse("core:order-detail", args=[self.order.id]))

    def test_the_customer_sees_the_tracking_number(self):
        self.order.tracking_id = "GHN123456789"
        self.order.save()

        self.assertContains(self._page(), "GHN123456789")

    def test_the_customer_is_told_when_there_is_no_number_yet(self):
        self.assertContains(self._page(), "Not assigned yet")
