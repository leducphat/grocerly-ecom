"""Làm sạch giỏ hàng — PLAN bước 2.3, SPEC-GAPS A4 (UC 3.2.6 Alternate Flow).

Xóa **từng** sản phẩm đã có sẵn từ trước (`delete_item_from_cart`) và vẫn chạy đúng;
cái thiếu là thao tác xóa **sạch toàn bộ** giỏ trong một lần. Cơ chế xóa sạch vốn đã tồn
tại ở ba chỗ trong `core/views.py` nhưng cả ba đều chạy sau khi thanh toán xong, nên
khách không gọi tới được.
"""

from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from core.models import CartOrder, Product
from userauths.models import User


class ClearCartTests(TestCase):

    def setUp(self):
        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), stock_count=10,
            product_status='published',
        )
        self.other = Product.objects.create(
            title="Xoài cát", price=Decimal("70000.00"), stock_count=10,
            product_status='published',
        )

    def _fill_cart(self):
        for product in (self.product, self.other):
            self.client.get(reverse("core:add-to-cart"), {'id': product.id, 'qty': 1})
        self.assertEqual(len(self.client.session['cart_data_obj']), 2)

    def _clear(self):
        return self.client.post(reverse("core:clear-cart"))

    def test_a_post_empties_the_whole_cart(self):
        self._fill_cart()

        self._clear()

        self.assertNotIn('cart_data_obj', self.client.session)

    def test_a_guest_can_clear_their_cart(self):
        """Giỏ nằm trong session, không có model Cart — khách vãng lai cũng có giỏ."""
        self._fill_cart()

        response = self._clear()

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('cart_data_obj', self.client.session)

    def test_clearing_an_empty_cart_does_not_blow_up(self):
        response = self._clear()

        self.assertEqual(response.status_code, 302)

    def test_the_user_is_told_the_cart_was_emptied(self):
        self._fill_cart()

        response = self._clear()

        texts = [str(m) for m in response.wsgi_request._messages]
        self.assertTrue(any("empt" in t.lower() or "trống" in t.lower() or "giỏ" in t.lower()
                            for t in texts), texts)

    def test_clearing_an_already_empty_cart_says_nothing(self):
        """Không có gì để xóa thì không báo là đã xóa."""
        response = self._clear()

        self.assertEqual([str(m) for m in response.wsgi_request._messages], [])

    # ---------- đơn treo ----------

    def test_the_pending_order_pointer_is_dropped(self):
        """Giữ lại con trỏ thì khách xóa sạch giỏ rồi bấm Thanh toán sẽ bị đá vào đúng
        cái đơn chứa những món vừa xóa."""
        user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(user)
        self._fill_cart()

        order = CartOrder.objects.create(user=user, price=Decimal("120000.00"))
        session = self.client.session
        session['pending_order_oid'] = str(order.oid)
        session.save()

        self._clear()

        self.assertNotIn('pending_order_oid', self.client.session)

    def test_the_unpaid_order_itself_is_not_cancelled(self):
        """Xóa giỏ **không phải** là hủy đơn — hủy đơn là A7 / PLAN bước 2.10."""
        user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(user)
        order = CartOrder.objects.create(user=user, price=Decimal("120000.00"))
        session = self.client.session
        session['pending_order_oid'] = str(order.oid)
        session.save()

        self._clear()

        self.assertTrue(CartOrder.objects.filter(pk=order.pk).exists())

    def test_checkout_no_longer_bounces_the_user_into_the_stale_order(self):
        user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(user)
        self._fill_cart()
        order = CartOrder.objects.create(user=user, price=Decimal("120000.00"))
        session = self.client.session
        session['pending_order_oid'] = str(order.oid)
        session.save()

        self._clear()
        response = self.client.get(reverse("core:checkout-info"))

        self.assertNotIn(f"/checkout/{order.oid}/", response.url)

    # ---------- thao tác phá hủy phải là POST + CSRF ----------

    def test_a_get_clears_nothing(self):
        self._fill_cart()

        response = self.client.get(reverse("core:clear-cart"))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(len(self.client.session['cart_data_obj']), 2)

    def test_a_post_without_a_csrf_token_clears_nothing(self):
        strict = Client(enforce_csrf_checks=True)
        strict.get(reverse("core:add-to-cart"), {'id': self.product.id, 'qty': 1})

        response = strict.post(reverse("core:clear-cart"))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(strict.session['cart_data_obj']), 1)


class ClearCartButtonTests(TestCase):
    """Nút phải có ở **cả hai** template giỏ hàng.

    `cart.html` và `core/async/cart-list.html` gần như là bản sao của nhau (96 dòng mỗi
    file). Bản async là thứ thay thế `#cart-list` sau mỗi lần xóa/sửa số lượng bằng AJAX
    — thiếu nút ở đó thì nó biến mất ngay sau khi khách xóa một sản phẩm.
    """

    def setUp(self):
        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), stock_count=10,
            product_status='published',
        )

    def _add(self):
        self.client.get(reverse("core:add-to-cart"), {'id': self.product.id, 'qty': 1})

    def test_the_cart_page_offers_the_button(self):
        self._add()

        response = self.client.get(reverse("core:cart"))
        html = response.content.decode()

        self.assertIn(f'action="{reverse("core:clear-cart")}"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('return confirm(', html)

    def test_the_button_survives_a_quantity_change(self):
        """Bản async được render lại sau mỗi lần đổi số lượng."""
        self._add()

        response = self.client.get(
            reverse("core:update-cart"), {'id': self.product.id, 'qty': 2}
        )
        html = response.json()['data']

        self.assertIn(f'action="{reverse("core:clear-cart")}"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_the_button_survives_deleting_another_product(self):
        """Phải kiểm **cả hai** chỗ render bản async, không chỉ `update_cart`.

        `delete_item_from_cart` và `update_cart` mỗi hàm gọi `render_to_string` riêng với
        context dựng riêng, nên token thiếu ở một chỗ mà chỗ kia vẫn đủ.
        """
        other = Product.objects.create(
            title="Xoài cát", price=Decimal("70000.00"), stock_count=10,
            product_status='published',
        )
        self._add()
        self.client.get(reverse("core:add-to-cart"), {'id': other.id, 'qty': 1})

        response = self.client.get(
            reverse("core:delete-from-cart"), {'id': other.id}
        )
        html = response.json()['data']

        self.assertIn(f'action="{reverse("core:clear-cart")}"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_an_empty_cart_does_not_offer_the_button(self):
        self._add()
        self.client.get(reverse("core:delete-from-cart"), {'id': self.product.id})

        response = self.client.get(
            reverse("core:update-cart"), {'id': self.product.id, 'qty': 1}
        )

        self.assertNotIn(f'action="{reverse("core:clear-cart")}"', response.json()['data'])
