"""Endpoint đổi dữ liệu phải dùng POST + CSRF — PLAN bước 2.14, [S-10](../../docs/SECURITY.md).

Năm endpoint trong nhóm này đổi dữ liệu của **người khác** bằng một GET không token:
đổi địa chỉ giao hàng mặc định, thêm/xóa wishlist, đăng xuất, và lật một đơn hàng sang
thanh toán online.

**Vì sao không phải "khai thác được ngay"** — và vì sao vẫn phải vá. `settings.py` không
đặt `SESSION_COOKIE_SAMESITE` nên Django 5.2 dùng mặc định `Lax`, mà `Lax` **không gửi
cookie** trên request xuyên site kiểu `<img>` / `<iframe>` / `fetch`. Vector drive-by vì
vậy đã bị chặn sẵn. Cái `Lax` **không** chặn là **điều hướng cả trang bằng GET** — nạn
nhân bấm một link. Đó là mức độ còn lại, và là mức mà POST + CSRF đóng hẳn.

Đọc kèm mục *Rà soát 2026-08-26* trong SECURITY.md: thấy một endpoint đổi dữ liệu bằng
GET là **chưa đủ để kết luận có lỗ hổng** — còn phải trả lời request của kẻ tấn công có
mang được cookie phiên tới không.

Bốn endpoint giỏ hàng (`add_to_cart`, `update_cart`, `delete_item_from_cart`,
`payment_completed_view`) **cố ý giữ nguyên GET**: chúng chỉ đụng session của chính người
gửi, nên không có dữ liệu của người khác để giả mạo. Ghi rõ ở `CartEndpointsStayOnGetTests`.
"""

from django.test import TestCase
from django.urls import reverse

from core.models import Address, CartOrder, Category, Product, Wishlist
from userauths.models import User


PASSWORD = 'grocerly-test-pw-9137'


class StateChangingEndpointTestCase(TestCase):
    """Nền chung: một khách đã đăng nhập, một sản phẩm còn bán."""

    def setUp(self):
        self.customer = User.objects.create_user(
            email='khach@grocerly.test', username='khach', password=PASSWORD,
        )
        self.client.force_login(self.customer)
        self.category = Category.objects.create(title='Rau')
        self.product = Product.objects.create(
            title='Cải ngọt', price=12000, category=self.category,
            product_status='published', stock_count=10,
        )


class MakeAddressDefaultTests(StateChangingEndpointTestCase):
    """Đổi địa chỉ giao hàng mặc định."""

    URL = reverse('core:make-default-address')

    def setUp(self):
        super().setUp()
        self.home = Address.objects.create(
            user=self.customer, address='12 Vo Van Ngan', status=True,
        )
        self.office = Address.objects.create(
            user=self.customer, address='1 Ly Thuong Kiet', status=False,
        )

    def test_a_get_no_longer_changes_anything(self):
        """Đây là kịch bản thật: nạn nhân bấm một link, địa chỉ giao hàng bị đổi.

        `SameSite=Lax` **có** gửi cookie trên điều hướng cả trang bằng GET, nên chốt duy
        nhất ở đây là bản thân method.
        """
        response = self.client.get(self.URL, {'id': self.office.id})
        self.assertEqual(response.status_code, 405)
        self.office.refresh_from_db()
        self.assertFalse(self.office.status)

    def test_a_post_still_works(self):
        response = self.client.post(self.URL, {'id': self.office.id})
        self.assertEqual(response.status_code, 200)
        self.office.refresh_from_db()
        self.home.refresh_from_db()
        self.assertTrue(self.office.status)
        self.assertFalse(self.home.status)

    def test_it_only_touches_the_senders_own_addresses(self):
        """Chốt sẵn có, giữ lại: `id` là khóa chính số nên đoán được."""
        intruder = User.objects.create_user(
            email='ke-la@grocerly.test', username='ke-la', password=PASSWORD,
        )
        self.client.force_login(intruder)
        self.client.post(self.URL, {'id': self.office.id})
        self.office.refresh_from_db()
        self.assertFalse(self.office.status)

    def test_it_requires_a_signed_in_user(self):
        self.client.logout()
        response = self.client.post(self.URL, {'id': self.office.id})
        self.assertEqual(response.status_code, 302)


class WishlistTests(StateChangingEndpointTestCase):
    """Thêm và xóa mục wishlist."""

    ADD_URL = reverse('core:add-to-wishlist')
    REMOVE_URL = reverse('core:remove-from-wishlist')

    def test_adding_by_get_no_longer_works(self):
        response = self.client.get(self.ADD_URL, {'id': self.product.id})
        self.assertEqual(response.status_code, 405)
        self.assertFalse(Wishlist.objects.filter(user=self.customer).exists())

    def test_adding_by_post_works(self):
        response = self.client.post(self.ADD_URL, {'id': self.product.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Wishlist.objects.filter(user=self.customer, product=self.product).exists()
        )

    def test_posting_twice_toggles_the_item_off(self):
        """Hành vi sẵn có: cùng một endpoint vừa thêm vừa bỏ."""
        self.client.post(self.ADD_URL, {'id': self.product.id})
        response = self.client.post(self.ADD_URL, {'id': self.product.id})
        self.assertFalse(response.json()['added'])
        self.assertFalse(Wishlist.objects.filter(user=self.customer).exists())

    def test_removing_by_get_no_longer_works(self):
        item = Wishlist.objects.create(user=self.customer, product=self.product)
        response = self.client.get(self.REMOVE_URL, {'id': item.id})
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Wishlist.objects.filter(pk=item.pk).exists())

    def test_removing_by_post_works(self):
        item = Wishlist.objects.create(user=self.customer, product=self.product)
        response = self.client.post(self.REMOVE_URL, {'id': item.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Wishlist.objects.filter(pk=item.pk).exists())

    def test_removing_someone_elses_item_does_nothing(self):
        item = Wishlist.objects.create(user=self.customer, product=self.product)
        intruder = User.objects.create_user(
            email='ke-la@grocerly.test', username='ke-la', password=PASSWORD,
        )
        self.client.force_login(intruder)
        self.client.post(self.REMOVE_URL, {'id': item.id})
        self.assertTrue(Wishlist.objects.filter(pk=item.pk).exists())

    def test_an_anonymous_visitor_gets_the_json_error_not_a_redirect(self):
        """Hai endpoint này trả JSON cho JS chứ không dùng `@login_required` — widget
        wishlist đọc `error` để hiện lời nhắc đăng nhập."""
        self.client.logout()
        response = self.client.post(self.ADD_URL, {'id': self.product.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['bool'])


class LogoutTests(StateChangingEndpointTestCase):
    """Đăng xuất — GET là đá được nạn nhân khỏi phiên bằng một link."""

    URL = reverse('userauths:sign-out')

    def test_a_get_no_longer_ends_the_session(self):
        """Mất phiên là mất luôn giỏ hàng đang giữ trong session (bẫy #7)."""
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_a_post_ends_the_session(self):
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_it_still_redirects_to_the_sign_in_page(self):
        self.assertEqual(
            self.client.post(self.URL).url, reverse('userauths:sign-in'),
        )


class VnpayPaymentMethodTests(StateChangingEndpointTestCase):
    """Chuyển sang cổng thanh toán — GET là lật được đơn của nạn nhân sang `online`."""

    def setUp(self):
        super().setUp()
        self.order = CartOrder.objects.create(
            user=self.customer, price=120000, paid_status=False,
        )
        self.session_set_pending(self.order)
        self.URL = reverse('core:vnpay_payment', args=[self.order.oid])

    def session_set_pending(self, order):
        session = self.client.session
        session['pending_order_oid'] = str(order.oid)
        session.save()

    def test_a_get_no_longer_flips_the_order(self):
        """Chốt duy nhất trước đây là không có chốt nào: view gán thẳng
        `payment_method='online'` và `product_status='processing'`.

        ⚠️ Đơn ở đây cố tình dựng ở `shipped`, không phải giá trị mặc định. **Cả hai**
        field mà view này ghi đều đã mang sẵn giá trị-sau-khi-chạy ngay từ lúc tạo đơn:
        `payment_method` mặc định `'online'` và `product_status` mặc định `'processing'`.
        Hai bản đầu của test đều đỏ vì khẳng định vào chúng — không phải vì code sai mà
        vì **không quan sát được gì**. Khẳng định 405 rồi thôi thì tệ hơn nữa: đó đúng là
        test trang trí. `shipped` là trạng thái duy nhất trong nhóm này mà view sẽ ghi đè
        nếu nó thật sự chạy, và không vướng chốt nào của chính view đó.
        """
        self.order.product_status = 'shipped'
        self.order.save(update_fields=['product_status'])

        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 405)
        self.order.refresh_from_db()
        self.assertEqual(self.order.product_status, 'shipped')

    def test_a_post_redirects_to_the_gateway(self):
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_method, 'online')
        self.assertEqual(self.order.product_status, 'processing')

    def test_it_requires_a_signed_in_user(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.URL).status_code, 302)


class SignOutControlIsAFormTests(StateChangingEndpointTestCase):
    """Nút đăng xuất phải là form POST, không phải `<a href>`.

    Chuyển `logout_view` sang POST-only mà quên sửa template thì nút vẫn hiện, vẫn bấm
    được, và trả về **405** — hỏng hoàn toàn nhưng không test nào ở tầng view thấy.

    Cám dỗ ngược lại cũng có thật: nút form khó style hơn link, nên "sửa cho đẹp" bằng
    cách trả về `<a href>` là mở lại đúng lỗ hổng. Đó là lý do có nhóm này.
    """

    def assert_sign_out_is_a_form(self, response):
        html = response.content.decode()
        self.assertIn(f'action="{reverse("userauths:sign-out")}" method="post"', html)
        self.assertNotIn(f'href="{reverse("userauths:sign-out")}"', html)

    def test_the_storefront_header_posts_to_sign_out(self):
        self.assert_sign_out_is_a_form(self.client.get(reverse('core:index')))

    def test_the_customer_dashboard_posts_to_sign_out(self):
        self.assert_sign_out_is_a_form(self.client.get(reverse('core:dashboard')))

    def test_the_staff_dashboard_posts_to_sign_out(self):
        staff = User.objects.create_user(
            email='nhanvien@grocerly.test', username='nhanvien', password=PASSWORD,
        )
        staff.is_staff = True
        staff.save()
        self.client.force_login(staff)
        self.assert_sign_out_is_a_form(self.client.get(reverse('useradmin:dashboard')))


class VnpayButtonIsAFormTests(StateChangingEndpointTestCase):
    """Nút "Thanh toán qua VNPay" cũng vậy — cùng lý do, cùng cám dỗ."""

    def test_the_checkout_page_posts_to_the_gateway(self):
        order = CartOrder.objects.create(user=self.customer, price=120000)
        session = self.client.session
        session['pending_order_oid'] = str(order.oid)
        session.save()

        html = self.client.get(reverse('core:checkout', args=[order.oid])).content.decode()
        url = reverse('core:vnpay_payment', args=[order.oid])
        self.assertIn(f'action="{url}" method="POST"', html)
        self.assertNotIn(f'href="{url}"', html)


class CartEndpointsStayOnGetTests(StateChangingEndpointTestCase):
    """Bốn endpoint giỏ hàng **cố ý** vẫn nhận GET.

    Không phải sót. Chúng chỉ đọc-ghi `request.session['cart_data_obj']` của **chính
    người gửi**, nên không có dữ liệu của người khác để giả mạo: ép một nạn nhân thêm
    món vào giỏ của chính họ không phải là tấn công, và giỏ hàng không cần đăng nhập nên
    khách vãng lai cũng phải dùng được.

    Test này tồn tại để lần sau ai đọc S-10 rồi thấy chúng còn GET thì biết ngay là đã
    cân nhắc, chứ không phải bỏ quên. Đổi ý thì sửa cả JS trong `templates/partials/base.html`.
    """

    def test_add_to_cart_still_accepts_get(self):
        response = self.client.get(
            reverse('core:add-to-cart'), {'id': self.product.id, 'qty': 2},
        )
        self.assertEqual(response.status_code, 200)

    def test_update_cart_still_accepts_get(self):
        self.client.get(reverse('core:add-to-cart'), {'id': self.product.id, 'qty': 2})
        response = self.client.get(
            reverse('core:update-cart'), {'id': self.product.id, 'qty': 3},
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_item_from_cart_still_accepts_get(self):
        self.client.get(reverse('core:add-to-cart'), {'id': self.product.id, 'qty': 2})
        response = self.client.get(
            reverse('core:delete-from-cart'), {'id': self.product.id},
        )
        self.assertEqual(response.status_code, 200)
