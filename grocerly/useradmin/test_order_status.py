"""Đổi trạng thái đơn hàng — PLAN bước 2.2, SPEC-GAPS A8 (UC 3.2.20 Exception Flow).

Trước đây `change_order_status` không kiểm gì cả: nhận mọi chuỗi từ POST, gán thẳng vào
`CartOrder.product_status`, và cho phép chuyển ngược từ `delivered` về `processing`.

⚠️ `CartOrder.product_status` là trạng thái GIAO HÀNG (`processing`/`shipped`/
`delivered`), **không phải** `Product.product_status` là trạng thái đăng bán. Hai field
trùng tên, khác nghĩa hoàn toàn — Bẫy #1 trong AGENTS.md.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, CartOrderItem, Product
from userauths.models import User


class ChangeOrderStatusTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username="nhanvien", email="nhanvien@grocerly.vn", password="matkhau123",
            is_staff=True,
        )
        self.client.force_login(self.staff)

        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), stock_count=10,
            product_status='published',
        )
        self.order = CartOrder.objects.create(
            user=self.staff, price=Decimal("100000.00"), product_status='processing',
        )
        CartOrderItem.objects.create(
            order=self.order,
            # Khóa ngoại là thứ `change_order_status` trừ kho theo, từ PLAN bước 2.11
            # (ADR-0006). `item` vẫn giữ để bản sao tĩnh của hóa đơn không đổi nghĩa —
            # nhưng nó không còn là đường tra ngược nữa.
            product=self.product,
            invoice_no=f"INVOICE_NO-{self.order.id}",
            item=self.product.title,
            image="/media/products.jpg",
            quantity=2,
            price=self.product.price,
            total=Decimal("100000.00"),
        )

    def _set(self, status):
        return self.client.post(
            reverse("useradmin:change_order_status", args=[self.order.oid]),
            {'status': status},
        )

    def _reload(self):
        self.order.refresh_from_db()
        self.product.refresh_from_db()

    # ---------- luồng bình thường ----------

    def test_processing_to_shipped_moves_the_order_and_takes_stock(self):
        self._set('shipped')
        self._reload()

        self.assertEqual(self.order.product_status, 'shipped')
        self.assertEqual(self.product.stock_count, 8)

    def test_shipped_to_delivered_marks_a_cod_order_paid(self):
        self.order.payment_method = 'cod'
        self.order.product_status = 'shipped'
        self.order.save()

        self._set('delivered')
        self._reload()

        self.assertEqual(self.order.product_status, 'delivered')
        self.assertTrue(self.order.paid_status)

    def test_delivering_an_online_order_does_not_touch_paid_status(self):
        """Đơn online chỉ được đánh dấu đã trả bởi vnpay_return/vnpay_ipn — SECURITY.md S-01."""
        self.order.payment_method = 'online'
        self.order.product_status = 'shipped'
        self.order.save()

        self._set('delivered')
        self._reload()

        self.assertFalse(self.order.paid_status)

    # ---------- A8: đã giao là trạng thái cuối ----------

    def test_a_delivered_order_cannot_be_moved_back(self):
        self.order.product_status = 'delivered'
        self.order.save()

        self._set('processing')
        self._reload()

        self.assertEqual(self.order.product_status, 'delivered')

    def test_a_delivered_order_cannot_be_set_to_delivered_again(self):
        self.order.product_status = 'delivered'
        self.order.save()

        response = self._set('delivered')

        self.assertEqual(response.status_code, 302)
        self._reload()
        self.assertEqual(self.order.product_status, 'delivered')

    def test_moving_a_delivered_order_back_does_not_take_stock_twice(self):
        """Lỗi trừ kho hai lần mà A8 chặn được.

        Điều kiện cũ là `status == 'shipped' and order.product_status != 'shipped'`, nên
        delivered → shipped bị coi là một lần giao mới và trừ kho thêm lần nữa cho cùng
        một đơn hàng.
        """
        self._set('shipped')
        self._reload()
        self.assertEqual(self.product.stock_count, 8)

        self._set('delivered')
        self._set('shipped')
        self._reload()

        self.assertEqual(self.product.stock_count, 8, "Kho chỉ được trừ một lần cho mỗi đơn")

    def test_marking_an_already_shipped_order_shipped_again_takes_no_extra_stock(self):
        self._set('shipped')
        self._reload()
        self.assertEqual(self.product.stock_count, 8)

        self._set('shipped')
        self._reload()

        self.assertEqual(self.product.stock_count, 8)

    def test_an_order_stuck_on_a_legacy_bad_status_still_takes_stock_when_shipped(self):
        """Đơn mắc kẹt ở 'pending' vẫn phải trừ kho khi được cứu về `shipped`.

        Trước khi vá, dropdown gửi value="pending" nên production có thể còn đơn ở giá
        trị rác đó. Chúng **chưa** xuất kho, nên điều kiện trừ kho không được viết hẹp
        thành `== 'processing'` — làm vậy là những đơn này giao đi mà kho không giảm.
        """
        # `choices` không được ép ở tầng database nên vẫn dựng lại được tình huống cũ.
        CartOrder.objects.filter(pk=self.order.pk).update(product_status='pending')

        self._set('shipped')
        self._reload()

        self.assertEqual(self.order.product_status, 'shipped')
        self.assertEqual(self.product.stock_count, 8)

    # ---------- 2.11: trừ kho theo khóa ngoại, không theo tên ----------

    def test_shipping_takes_stock_from_the_product_that_was_actually_bought(self):
        """Nợ kỹ thuật #6 — chốt lại bằng test (PLAN bước 2.11, ADR-0006).

        Trước đây chỗ này chạy `Product.objects.filter(title=item.item).first()`. Hai sản
        phẩm trùng tên thì `.first()` trả về cái có `id` nhỏ hơn, **không phải** cái khách
        mua — trừ kho của một sản phẩm chưa hề bán được món nào.

        Ở đây `twin` được tạo TRƯỚC để nó đứng đầu theo `id`: có vậy test mới bắt được
        lỗi cũ thay vì tình cờ đi qua.
        """
        twin = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), stock_count=100,
            product_status='published',
        )
        bought = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), stock_count=10,
            product_status='published',
        )
        order = CartOrder.objects.create(
            user=self.staff, price=Decimal("100000.00"), product_status='processing',
        )
        CartOrderItem.objects.create(
            order=order, product=bought, invoice_no=f"INVOICE_NO-{order.id}",
            item=bought.title, image="/media/products.jpg",
            quantity=2, price=bought.price, total=Decimal("100000.00"),
        )

        self.client.post(
            reverse("useradmin:change_order_status", args=[order.oid]),
            {'status': 'shipped'},
        )

        bought.refresh_from_db()
        twin.refresh_from_db()
        self.assertEqual(bought.stock_count, 8)
        self.assertEqual(twin.stock_count, 100)   # không bị đụng tới

    def test_renaming_a_product_after_the_sale_does_not_break_stock_deduction(self):
        """Chiều còn lại của cùng một lỗi: đổi tên xong thì khớp theo tên hụt hoàn toàn."""
        self.product.title = "Dưa hấu không hạt"
        self.product.save()

        self._set('shipped')
        self._reload()

        self.assertEqual(self.product.stock_count, 8)

    def test_a_legacy_line_without_a_link_is_skipped_instead_of_guessing(self):
        """Dòng có từ trước migration 0007 mà backfill không dò ra sản phẩm gốc.

        Không trừ kho, và **không** quay lại đoán theo tên: ở đây đoán sai nghĩa là trừ
        kho của một sản phẩm khác. Quan trọng nhất là đơn vẫn chuyển trạng thái bình
        thường chứ không nổ.
        """
        CartOrderItem.objects.filter(order=self.order).update(product=None)

        response = self._set('shipped')
        self._reload()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.product_status, 'shipped')
        self.assertEqual(self.product.stock_count, 10)

    def test_shipping_still_works_when_the_product_was_erased(self):
        """Sản phẩm bị xóa cứng sau khi bán → khóa ngoại về NULL. Không được làm sập."""
        self.product.hard_delete()

        response = self._set('shipped')
        self.order.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.order.product_status, 'shipped')

    # ---------- trạng thái không hợp lệ ----------

    def test_the_pending_placeholder_no_longer_corrupts_the_order(self):
        """Option đầu của dropdown từng gửi value="pending".

        'pending' không nằm trong STATUS_CHOICES, mà view gán thẳng không kiểm — nên chỉ
        cần bấm Save khi chưa chọn gì là đơn rơi vào trạng thái không hợp lệ.
        """
        self._set('pending')
        self._reload()

        self.assertEqual(self.order.product_status, 'processing')

    def test_an_arbitrary_string_is_rejected(self):
        self._set('rac-tuy-y')
        self._reload()

        self.assertEqual(self.order.product_status, 'processing')

    def test_an_empty_status_is_rejected(self):
        self._set('')
        self._reload()

        self.assertEqual(self.order.product_status, 'processing')

    # ---------- method, CSRF, phân quyền ----------

    def test_a_get_request_changes_nothing(self):
        response = self.client.get(
            reverse("useradmin:change_order_status", args=[self.order.oid])
        )

        self.assertEqual(response.status_code, 405)
        self._reload()
        self.assertEqual(self.order.product_status, 'processing')

    def test_a_post_without_a_csrf_token_changes_nothing(self):
        """View từng có @csrf_exempt dù template đã gửi kèm token."""
        from django.test import Client

        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)

        response = strict.post(
            reverse("useradmin:change_order_status", args=[self.order.oid]),
            {'status': 'shipped'},
        )

        self.assertEqual(response.status_code, 403)
        self._reload()
        self.assertEqual(self.order.product_status, 'processing')

    def test_a_customer_cannot_change_an_order_status(self):
        self.client.logout()
        khach = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(khach)

        self._set('delivered')
        self._reload()

        self.assertEqual(self.order.product_status, 'processing')

    def test_an_unknown_order_returns_404_instead_of_crashing(self):
        response = self.client.post(
            reverse("useradmin:change_order_status", args=["khong-co-that"]),
            {'status': 'shipped'},
        )

        self.assertEqual(response.status_code, 404)


class OrderDetailFormTests(TestCase):
    """Dropdown phải dựng từ model và khóa lại khi đơn đã giao."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="nhanvien", email="nhanvien@grocerly.vn", password="matkhau123",
            is_staff=True,
        )
        self.client.force_login(self.staff)
        self.order = CartOrder.objects.create(
            user=self.staff, price=Decimal("100000.00"), product_status='processing',
        )

    def _page(self):
        return self.client.get(reverse("useradmin:order_detail", args=[self.order.id]))

    def test_the_placeholder_option_posts_nothing(self):
        response = self._page()

        self.assertContains(response, '<option value="">')
        self.assertNotContains(response, 'value="pending"')

    def test_every_valid_status_is_offered(self):
        response = self._page()

        for value in ('processing', 'shipped', 'delivered'):
            self.assertContains(response, f'value="{value}"')

    def test_the_current_status_is_preselected(self):
        response = self._page()

        self.assertContains(response, 'value="processing" selected')

    def test_the_form_is_disabled_once_the_order_is_delivered(self):
        self.order.product_status = 'delivered'
        self.order.save()

        response = self._page()

        self.assertContains(response, 'disabled')
        self.assertContains(response, "Its status is final")
