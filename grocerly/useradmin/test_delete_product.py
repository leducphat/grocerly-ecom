"""Xóa sản phẩm ở dashboard nhân viên — PLAN bước 2.1, SPEC-GAPS B3.

Hình 30 trong báo cáo vẽ nhánh: kiểm tra đơn hàng liên quan rồi mới quyết xóa mềm hay
xóa cứng. Code trước đây gọi thẳng `product.delete()`, mà `SoftDeleteModel` không
override `delete()` ở tầng instance (**Bẫy #3**) nên nó xóa cứng vô điều kiện — kể cả
sản phẩm đã bán.

Hành vi nền của chính cơ chế xóa mềm nằm ở `core/test_softdelete.py`; file này chỉ lo
phần *quyết định* của view.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, CartOrderItem, Product
from userauths.models import User


class DeleteProductTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username="nhanvien", email="nhanvien@grocerly.vn", password="matkhau123",
            is_staff=True,
        )
        self.client.force_login(self.staff)

        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), product_status='published',
        )

    def _delete(self, product=None):
        product = product or self.product
        return self.client.post(
            reverse("useradmin:dashboard-delete-products", args=[product.p_id])
        )

    def _sell(self, product, title=None):
        """Tạo một dòng đơn hàng trỏ tới sản phẩm, đúng cách `save_checkout_info` làm."""
        order = CartOrder.objects.create(user=self.staff, price=Decimal("50000.00"))
        return CartOrderItem.objects.create(
            order=order,
            invoice_no=f"INVOICE_NO-{order.id}",
            item=title if title is not None else product.title,
            image="/media/products.jpg",
            quantity=1,
            price=product.price,
            total=product.price,
        )

    # ---------- sản phẩm chưa từng bán ----------

    def test_a_product_with_no_orders_is_erased(self):
        pk = self.product.pk

        self._delete()

        self.assertFalse(Product.all_objects.filter(pk=pk).exists())

    # ---------- sản phẩm đã bán ----------

    def test_a_sold_product_is_hidden_not_erased(self):
        self._sell(self.product)
        pk = self.product.pk

        self._delete()

        self.assertFalse(Product.objects.filter(pk=pk).exists())
        self.assertTrue(Product.all_objects.filter(pk=pk).exists())

    def test_a_sold_product_disappears_from_the_storefront(self):
        """Xóa mềm phải có tác dụng thật, không chỉ là một cờ trong database."""
        self._sell(self.product)

        self._delete()

        self.assertNotIn(self.product, Product.objects.published())

        # Phải thoát tài khoản nhân viên trước khi xem storefront:
        # `RestrictStaffMiddleware` đá staff về trang quản trị (Bẫy #6), nên nếu giữ
        # nguyên phiên đăng nhập thì nhận 302 chứ không phải trang tìm kiếm.
        self.client.logout()
        response = self.client.get(reverse("core:search"), {'q': "Dưa hấu"})

        self.assertEqual(response.status_code, 200)
        # Kiểm bằng context chứ không bằng chuỗi HTML: trang tìm kiếm in lại chính từ
        # khóa người dùng gõ, nên `assertNotContains(response, "Dưa hấu")` luôn đỏ kể cả
        # khi không còn sản phẩm nào.
        self.assertEqual(list(response.context['products']), [])

    def test_the_invoice_still_shows_what_the_customer_bought(self):
        """Lý do tồn tại của bản sao tĩnh trong `CartOrderItem`."""
        item = self._sell(self.product)

        self._delete()

        item.refresh_from_db()
        self.assertEqual(item.item, "Dưa hấu")
        self.assertEqual(item.price, Decimal("50000.00"))

    def test_a_soft_deleted_product_can_be_restored(self):
        self._sell(self.product)
        self._delete()

        hidden = Product.all_objects.get(pk=self.product.pk)
        hidden.restore()

        self.assertIn(hidden, Product.objects.published())

    # ---------- ranh giới của việc khớp theo tên ----------

    def test_an_order_for_a_different_product_does_not_protect_this_one(self):
        other = Product.objects.create(title="Xoài cát", price=Decimal("70000.00"))
        self._sell(other)
        pk = self.product.pk

        self._delete()

        self.assertFalse(Product.all_objects.filter(pk=pk).exists())

    def test_a_same_named_product_protects_this_one_too(self):
        """Nhầm về phía AN TOÀN, và chốt lại đây là hệ quả của việc khớp theo tên.

        `CartOrderItem` chưa có khóa ngoại tới `Product` (ADR-0006, PLAN bước 2.11) nên
        chỉ so được theo tên. Hai sản phẩm trùng tên thì bán cái này lại bảo vệ cái kia
        — xóa mềm thay vì xóa cứng, tức là nhầm về phía giữ lại dữ liệu.

        Khi bước 2.11 xong, test này phải đổi kỳ vọng: lúc đó phân biệt được đúng sản
        phẩm nên bản chưa bán sẽ bị xóa cứng.
        """
        twin = Product.objects.create(title="Dưa hấu", price=Decimal("50000.00"))
        self._sell(twin)
        pk = self.product.pk

        self._delete()

        self.assertTrue(Product.all_objects.filter(pk=pk).exists())

    # ---------- phân quyền và đầu vào hỏng ----------

    def test_a_customer_cannot_delete_anything(self):
        self.client.logout()
        khach = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(khach)
        pk = self.product.pk

        self._delete()

        self.assertTrue(Product.all_objects.filter(pk=pk).exists())

    def test_an_unknown_product_id_returns_404_instead_of_crashing(self):
        # Trước đây là `Product.objects.get(...)` trần → DoesNotExist → lỗi 500.
        response = self.client.post(
            reverse("useradmin:dashboard-delete-products", args=["khong-co-that"])
        )

        self.assertEqual(response.status_code, 404)

    # ---------- thao tác phá hủy phải là POST + CSRF ----------

    def test_a_get_request_deletes_nothing(self):
        """Trước đây nút Delete là `<a href>`, tức là xóa được bằng một request GET.

        Nghĩa là trình duyệt prefetch link, hay chỉ cần dụ nhân viên đang đăng nhập click
        vào một URL, là xóa được sản phẩm.
        """
        pk = self.product.pk

        response = self.client.get(
            reverse("useradmin:dashboard-delete-products", args=[self.product.p_id])
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Product.all_objects.filter(pk=pk).exists())

    def test_a_post_without_a_csrf_token_deletes_nothing(self):
        from django.test import Client

        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.staff)
        pk = self.product.pk

        response = strict.post(
            reverse("useradmin:dashboard-delete-products", args=[self.product.p_id])
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Product.all_objects.filter(pk=pk).exists())

    def test_the_product_list_posts_the_delete_with_a_csrf_token(self):
        """Chốt cả phía giao diện: nếu ai đó đổi form về `<a href>` thì test này đỏ."""
        response = self.client.get(reverse("useradmin:dashboard-products"))
        html = response.content.decode()
        action = reverse("useradmin:dashboard-delete-products", args=[self.product.p_id])

        self.assertIn(f'action="{action}"', html)
        self.assertNotIn(f'href="{action}"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_the_delete_button_asks_for_confirmation(self):
        response = self.client.get(reverse("useradmin:dashboard-products"))

        self.assertContains(response, "return confirm(")

    def test_a_quote_in_the_product_name_does_not_break_the_confirm_dialog(self):
        """Tên sản phẩm do nhân viên nhập rồi được đưa vào câu xác nhận.

        Nhét thẳng vào chuỗi JS thì phải escape hai tầng và người dùng **đọc được**
        `&#x27;` thay vì dấu nháy. Đưa qua `data-confirm` thì chỉ escape một tầng, và
        trình duyệt tự giải mã khi JS đọc `this.dataset.confirm`.
        """
        Product.objects.create(title="Nước mắm 'Ông Kỳ' 500ml", price=Decimal("60000.00"))

        response = self.client.get(reverse("useradmin:dashboard-products"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        # Escape đúng MỘT tầng HTML. Nếu nhét vào chuỗi JS thì ra `\\u0026#x27\\u003B`
        # — an toàn nhưng người dùng đọc được rác đó trong hộp thoại.
        self.assertNotIn("\\u0026#x27", html)
        # Cả thuộc tính còn nguyên vẹn, không bị dấu nháy trong tên sản phẩm đóng sớm.
        self.assertIn(
            'data-confirm="Delete “Nước mắm &#x27;Ông Kỳ&#x27; 500ml”? '
            'A product that has never been ordered is erased permanently '
            'and cannot be recovered."',
            html,
        )

    def test_deleting_an_already_hidden_product_returns_404(self):
        """`Product.objects` đã lọc bản ghi xóa mềm, nên không xóa mềm hai lần được."""
        self._sell(self.product)
        self._delete()

        response = self._delete()

        self.assertEqual(response.status_code, 404)
