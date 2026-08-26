"""Unit test cho hai middleware tự viết — PLAN bước 2.6e.

Hai lớp này không nằm trong app nào rõ ràng (`grocerly/middleware.py` và
`core/middleware.py`), không có test nào, mà lại quyết định **ai vào được trang nào** và
**trang hiện ngôn ngữ gì**. `RestrictStaffMiddleware` chính là **bẫy #6** trong
[AGENTS.md](../../AGENTS.md): quên nó là mọi test luồng khách hàng viết bằng tài khoản
staff đều sai mà không hiểu vì sao.

Phần lớn là `SimpleTestCase` với `RequestFactory` và một `get_response` giả — không dựng
database, không đi qua toàn bộ chồng middleware. Nhóm cuối cùng là ngoại lệ có chủ ý:
[MiddlewareOrderTests](#) khẳng định **thứ tự** trong `settings.MIDDLEWARE`, thứ mà không
test đơn lẻ nào phát hiện được nếu ai đó sắp xếp lại danh sách.
"""

from types import SimpleNamespace

from django.conf import settings
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from core.middleware import ForceDefaultLanguageMiddleware
from grocerly.middleware import RestrictStaffMiddleware
from userauths.models import User


SENTINEL = object()


def passthrough(request):
    """`get_response` giả — trả về một vật thể nhận dạng được.

    Nhận đúng `SENTINEL` nghĩa là middleware đã cho request đi tiếp; nhận
    `HttpResponseRedirect` nghĩa là nó đã chặn lại.
    """
    return SENTINEL


def anonymous():
    return SimpleNamespace(is_authenticated=False, is_staff=False, is_superuser=False)


def customer():
    return SimpleNamespace(is_authenticated=True, is_staff=False, is_superuser=False)


def staff():
    return SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=False)


def admin():
    return SimpleNamespace(is_authenticated=True, is_staff=True, is_superuser=True)


class RestrictStaffMiddlewarePassThroughTests(SimpleTestCase):
    """Ai được đi tiếp bình thường."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RestrictStaffMiddleware(passthrough)

    def get(self, path, user):
        request = self.factory.get(path)
        request.user = user
        return self.middleware(request)

    def test_an_anonymous_visitor_reaches_the_storefront(self):
        self.assertIs(self.get('/vi/', anonymous()), SENTINEL)

    def test_a_logged_in_customer_reaches_the_storefront(self):
        self.assertIs(self.get('/vi/', customer()), SENTINEL)

    def test_a_customer_reaches_the_cart(self):
        self.assertIs(self.get('/vi/cart/', customer()), SENTINEL)


class RestrictStaffMiddlewareRedirectTests(SimpleTestCase):
    """Nhân viên và quản trị viên bị đá khỏi storefront — **bẫy #6**."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RestrictStaffMiddleware(passthrough)

    def get(self, path, user):
        request = self.factory.get(path)
        request.user = user
        return self.middleware(request)

    def test_staff_visiting_the_storefront_land_on_their_dashboard(self):
        response = self.get('/vi/', staff())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('useradmin:dashboard'))

    def test_a_superuser_visiting_the_storefront_lands_on_django_admin(self):
        response = self.get('/vi/', admin())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/admin/')

    def test_the_superuser_branch_wins_over_the_staff_branch(self):
        """Quản trị viên cũng có `is_staff=True`, nên thứ tự hai nhánh là có ý nghĩa."""
        self.assertEqual(self.get('/vi/', admin()).url, '/admin/')

    def test_staff_are_redirected_away_from_the_cart_too(self):
        self.assertEqual(self.get('/vi/cart/', staff()).status_code, 302)

    def test_staff_are_redirected_from_an_unprefixed_path(self):
        self.assertEqual(self.get('/', staff()).status_code, 302)


class RestrictStaffMiddlewareAllowedPrefixTests(SimpleTestCase):
    """Những tiền tố nhân viên vẫn phải vào được."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RestrictStaffMiddleware(passthrough)

    def get(self, path, user=None):
        request = self.factory.get(path)
        request.user = user or staff()
        return self.middleware(request)

    def test_staff_reach_their_own_dashboard(self):
        self.assertIs(self.get('/useradmin/'), SENTINEL)

    def test_staff_reach_the_language_prefixed_dashboard(self):
        """Đường thật mà trình duyệt đi: `i18n_patterns` gắn tiền tố ngôn ngữ (bẫy #8)."""
        self.assertIs(self.get('/vi/useradmin/'), SENTINEL)
        self.assertIs(self.get('/en/useradmin/'), SENTINEL)

    def test_a_superuser_reaches_django_admin(self):
        self.assertIs(self.get('/admin/', admin()), SENTINEL)

    def test_staff_can_still_sign_out(self):
        """Thiếu tiền tố này là nhân viên **không đăng xuất được**: mọi lần bấm Sign out
        đều bị đá ngược về dashboard, và chỉ thoát được bằng cách xóa cookie."""
        self.assertIs(self.get('/vi/user/sign-out/'), SENTINEL)

    def test_static_and_media_are_not_redirected(self):
        self.assertIs(self.get('/static/assets/css/style.css'), SENTINEL)
        self.assertIs(self.get('/media/image/product.png'), SENTINEL)

    def test_every_configured_language_has_a_dashboard_prefix(self):
        """Danh sách tiền tố **liệt kê tay** `/vi/` và `/en/`, không dựng từ settings.

        Thêm một ngôn ngữ thứ ba vào `LANGUAGES` mà quên sửa `allowed_prefixes` là nhân
        viên mất hẳn đường vào dashboard ở ngôn ngữ đó — vòng lặp chuyển hướng, vì chính
        trang đích cũng bị chặn. Test này đỏ ngay lúc thêm ngôn ngữ, chứ không đợi tới
        lúc có người bấm.
        """
        for code, _label in settings.LANGUAGES:
            with self.subTest(language=code):
                self.assertIs(self.get(f'/{code}/useradmin/'), SENTINEL)

    def test_the_chatbot_api_is_not_on_the_allow_list(self):
        """Ghi lại một giới hạn đã biết, không phải khẳng định đây là hành vi mong muốn.

        `/api/v1/` nằm **ngoài** `i18n_patterns` và ngoài `allowed_prefixes`, nên nhân
        viên đang đăng nhập gọi trợ lý AI sẽ nhận `302` HTML thay vì JSON. Widget chat
        chỉ đọc `reply`/`error` nên sẽ hỏng im lặng — cùng kiểu lỗi đã gặp ở
        [S-03](../../docs/SECURITY.md).

        Chưa sửa vì chatbot là chức năng của **khách**, và nhân viên vốn không vào được
        trang nào có widget. Nếu sau này gắn trợ lý vào trang quản trị thì đây là chỗ
        phải sửa đầu tiên.
        """
        self.assertEqual(self.get('/api/v1/chat/').status_code, 302)


class RestrictStaffMiddlewareIntegrationTests(TestCase):
    """Một lượt qua **toàn bộ** chồng middleware, với tài khoản thật trong database.

    Ba nhóm trên chứng minh lớp middleware đúng khi được gọi trực tiếp. Nhóm này chứng
    minh nó thật sự **được lắp vào** `settings.MIDDLEWARE` — hai chuyện khác nhau.

    ⚠️ **Không dùng `core:index` ở đây.** Bản đầu của nhóm này gọi trang chủ và vẫn xanh
    nguyên sau khi gỡ `RestrictStaffMiddleware` khỏi settings — đúng kiểu test trang trí
    mà [PLAN.md](../../docs/PLAN.md) bước 2.8/2.9 đã ghi lại: nó chạy qua đúng chức năng,
    chỉ là không chạy qua đúng nhánh. Lý do là `index()` **tự** chuyển hướng nhân viên ở
    `core/views.py`, trùng lặp với middleware. `core:product-list` không có nhánh đó, nên
    chỉ nó mới chứng minh được điều nhóm này khẳng định.
    """

    STOREFRONT = 'core:product-list'

    def setUp(self):
        self.staff_user = User.objects.create_user(
            email='staff@grocerly.test', username='staff', password='pw-for-test-only',
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

    def test_a_signed_in_staff_member_cannot_browse_the_storefront(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(self.STOREFRONT))
        self.assertEqual(response.status_code, 302)
        self.assertIn('useradmin', response.url)

    def test_a_signed_in_superuser_is_sent_to_django_admin(self):
        self.staff_user.is_superuser = True
        self.staff_user.save()
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse(self.STOREFRONT))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/admin/')

    def test_the_same_page_is_fine_for_an_anonymous_visitor(self):
        self.assertEqual(self.client.get(reverse(self.STOREFRONT)).status_code, 200)

    def test_the_home_page_redirects_staff_on_its_own_without_the_middleware(self):
        """Ghi lại sự **trùng lặp**, để lần sau không ai mất công dò lại như lần này.

        `index()` có sẵn nhánh chuyển hướng nhân viên từ trước khi middleware ra đời. Nó
        vô hại (hai lớp cùng đưa tới một chỗ) nhưng khiến trang chủ trở thành chỗ **không
        dùng để kiểm chứng middleware được**. Nếu ai đó dọn nhánh trùng này đi, test trên
        vẫn là lưới an toàn; còn nếu ai đó dọn middleware đi vì "trang chủ đã chặn rồi"
        thì toàn bộ phần còn lại của storefront hở.
        """
        self.client.force_login(self.staff_user)
        with self.settings(MIDDLEWARE=[
            middleware for middleware in settings.MIDDLEWARE
            if middleware != MiddlewareOrderTests.RESTRICT_STAFF
        ]):
            self.assertEqual(
                self.client.get(reverse(self.STOREFRONT)).status_code, 200,
                'Storefront lẽ ra phải mở cho nhân viên khi middleware bị gỡ — '
                'nếu không, test ở trên không chứng minh được điều gì.',
            )
            self.assertEqual(self.client.get(reverse('core:index')).status_code, 302)


class ForceDefaultLanguageMiddlewareTests(SimpleTestCase):
    """Bỏ qua `Accept-Language` để mặc định luôn là tiếng Việt."""

    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = ForceDefaultLanguageMiddleware(passthrough)

    def test_it_removes_the_accept_language_header(self):
        request = self.factory.get('/', HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')
        self.middleware(request)
        self.assertNotIn('HTTP_ACCEPT_LANGUAGE', request.META)

    def test_it_passes_the_request_on(self):
        request = self.factory.get('/', HTTP_ACCEPT_LANGUAGE='en-US')
        self.assertIs(self.middleware(request), SENTINEL)

    def test_a_request_without_the_header_passes_through_untouched(self):
        request = self.factory.get('/')
        self.assertIs(self.middleware(request), SENTINEL)
        self.assertNotIn('HTTP_ACCEPT_LANGUAGE', request.META)

    def test_it_leaves_other_headers_alone(self):
        request = self.factory.get(
            '/', HTTP_ACCEPT_LANGUAGE='en-US', HTTP_USER_AGENT='grocerly-tests',
        )
        self.middleware(request)
        self.assertEqual(request.META.get('HTTP_USER_AGENT'), 'grocerly-tests')

    def test_an_english_speaking_browser_still_gets_vietnamese(self):
        """Hành vi thật khách nhìn thấy: trình duyệt xin tiếng Anh, vẫn ra tiếng Việt.

        Đi qua cả chồng middleware nên chỉ có test này chứng minh được điều đó — bản
        `RequestFactory` ở trên chỉ chứng minh header bị xóa.
        """
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(f'/{settings.LANGUAGE_CODE}/'),
            f'Đã chuyển hướng tới {response.url}, mong đợi tiền tố '
            f'/{settings.LANGUAGE_CODE}/',
        )


class MiddlewareOrderTests(SimpleTestCase):
    """Thứ tự trong `settings.MIDDLEWARE` — ràng buộc không có gì khác bảo vệ.

    Cả hai khẳng định ở đây đều **không** phát hiện được bằng cách test từng lớp riêng:
    mỗi lớp vẫn đúng chức năng của nó, chỉ là chạy sai lúc.
    """

    FORCE_LANGUAGE = 'core.middleware.ForceDefaultLanguageMiddleware'
    LOCALE = 'django.middleware.locale.LocaleMiddleware'
    AUTHENTICATION = 'django.contrib.auth.middleware.AuthenticationMiddleware'
    RESTRICT_STAFF = 'grocerly.middleware.RestrictStaffMiddleware'

    def test_the_language_override_runs_before_django_reads_the_language(self):
        """`ForceDefaultLanguageMiddleware` xóa `Accept-Language`, `LocaleMiddleware`
        đọc nó. Đảo thứ tự là header đã bị đọc xong rồi mới bị xóa — không lỗi, không
        cảnh báo, chỉ là trang hiện tiếng Anh cho khách Việt."""
        self.assertLess(
            settings.MIDDLEWARE.index(self.FORCE_LANGUAGE),
            settings.MIDDLEWARE.index(self.LOCALE),
        )

    def test_the_staff_restriction_runs_after_the_user_is_known(self):
        """`RestrictStaffMiddleware` đọc `request.user`, mà `AuthenticationMiddleware`
        mới là thứ gắn thuộc tính đó vào request. Đặt trước nó thì mọi request ném
        `AttributeError` — hoặc tệ hơn, nếu ai đó "sửa" bằng `getattr(..., None)` thì
        **mọi nhân viên đều vào được storefront** mà không ai nhận ra."""
        self.assertGreater(
            settings.MIDDLEWARE.index(self.RESTRICT_STAFF),
            settings.MIDDLEWARE.index(self.AUTHENTICATION),
        )

    def test_both_custom_middleware_are_actually_installed(self):
        self.assertIn(self.FORCE_LANGUAGE, settings.MIDDLEWARE)
        self.assertIn(self.RESTRICT_STAFF, settings.MIDDLEWARE)
