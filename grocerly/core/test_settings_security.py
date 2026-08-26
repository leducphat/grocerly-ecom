"""Unit test cho hai quyết định bảo mật trong `settings.py` — PLAN bước 2.5 và 2.14.

Vá [S-05](../../docs/SECURITY.md) (`SECRET_KEY` có giá trị mặc định, `DEBUG` mặc định
bật) và [S-11](../../docs/SECURITY.md) (cookie phiên không có cờ `Secure`).

Hai quy tắc này **không test được bằng cách đọc `settings.SECRET_KEY`**: giá trị đó do
môi trường quyết định, nên khẳng định nó chỉ nói lên máy đang chạy test có `.env` gì.
Cái cần chốt là **luật suy ra giá trị**, và ở hai mức khác nhau:

- `settings.py` tách luật thành `_env_flag` và `_resolve_secret_key`; các test gọi thẳng
  hai hàm đó với môi trường giả.
- `reloaded_settings()` nạp lại cả module với môi trường giả, để kiểm **chỗ gọi**. Cần
  mức này vì lượt đột biến đầu tiên cho thấy mức trên không đủ: khôi phục đúng lỗ hổng
  S-05 bằng cách đổi giá trị mặc định ở chỗ gọi mà không test nào đỏ, do mọi test đều tự
  truyền mặc định vào lời gọi của chính nó.

`SimpleTestCase` — không hàm nào chạm database.
"""

import contextlib
import importlib
import os
from unittest import mock

import grocerly.settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from grocerly.settings import DEV_SECRET_KEY, _env_flag, _resolve_secret_key


def without_env(*names):
    """Môi trường giả **không có** các biến kể tên."""
    environ = {key: value for key, value in os.environ.items() if key not in names}
    return mock.patch.dict(os.environ, environ, clear=True)


@contextlib.contextmanager
def reloaded_settings(**environ):
    """Nạp lại `grocerly.settings` với đúng môi trường được truyền vào.

    Chỉ có cách này mới kiểm chứng được **chỗ gọi**, chứ không riêng hàm được gọi. Lượt
    đột biến đầu tiên cho thấy vì sao điều đó cần: đổi `_env_flag('DJANGO_DEBUG', '0')`
    ngược lại thành `'1'` — tức khôi phục đúng lỗ hổng S-05 — mà **không test nào đỏ**,
    vì mọi test đều tự truyền giá trị mặc định vào lời gọi của chính nó.

    `DJANGO_SKIP_DOTENV=1` là bắt buộc: không có nó thì `.env` của máy đang chạy ghi đè
    lại môi trường giả ngay trong lúc nạp, và phép thử vô nghĩa.

    Không đụng tới `django.conf.settings` đang chạy — `settings_test` đã sao chép giá trị
    sang đó từ lúc khởi động, nên nạp lại module gốc không ảnh hưởng phần còn lại của
    suite. Vẫn nạp lại lần cuối theo môi trường thật để module không kẹt ở trạng thái giả.
    """
    environ.setdefault('DJANGO_SKIP_DOTENV', '1')
    try:
        with mock.patch.dict(os.environ, environ, clear=True):
            yield importlib.reload(grocerly.settings)
    finally:
        importlib.reload(grocerly.settings)


class DebugFlagTests(SimpleTestCase):
    """`DJANGO_DEBUG` — an toàn theo mặc định.

    Trước bản vá, thiếu biến môi trường nghĩa là **bật** `DEBUG`, tức trang lỗi phơi
    traceback và toàn bộ cấu hình cho bất kỳ ai gõ một URL sai.
    """

    def test_a_missing_variable_means_debug_is_off(self):
        with without_env('DJANGO_DEBUG'):
            self.assertFalse(_env_flag('DJANGO_DEBUG', '0'))

    def test_one_turns_it_on(self):
        with mock.patch.dict(os.environ, {'DJANGO_DEBUG': '1'}):
            self.assertTrue(_env_flag('DJANGO_DEBUG', '0'))

    def test_zero_turns_it_off(self):
        with mock.patch.dict(os.environ, {'DJANGO_DEBUG': '0'}):
            self.assertFalse(_env_flag('DJANGO_DEBUG', '0'))

    def test_stray_whitespace_does_not_flip_the_flag(self):
        """`.env` được nạp bằng `split('=', 1)` thủ công nên giá trị **giữ nguyên khoảng
        trắng thừa**. `DJANGO_DEBUG=1 ` với một dấu cách ở cuối từng là `False`."""
        with mock.patch.dict(os.environ, {'DJANGO_DEBUG': ' 1 '}):
            self.assertTrue(_env_flag('DJANGO_DEBUG', '0'))

    def test_anything_else_is_off(self):
        for value in ('true', 'True', 'yes', 'on', '2', ''):
            with self.subTest(value=value):
                with mock.patch.dict(os.environ, {'DJANGO_DEBUG': value}):
                    self.assertFalse(_env_flag('DJANGO_DEBUG', '0'))


class SecretKeyTests(SimpleTestCase):
    """`DJANGO_SECRET_KEY` — thiếu ở production là **không được khởi động**."""

    def test_the_environment_variable_wins(self):
        with mock.patch.dict(os.environ, {'DJANGO_SECRET_KEY': 'khoa-that'}):
            self.assertEqual(_resolve_secret_key(debug=False), 'khoa-that')

    def test_production_refuses_to_start_without_one(self):
        """Đây là toàn bộ mục đích của bản vá.

        Trước đây thiếu biến thì ứng dụng vẫn chạy bình thường bằng khóa mặc định — mà
        khóa đó **đã nằm công khai trên GitHub**. `SECRET_KEY` ký cookie phiên và token
        đặt lại mật khẩu, nên biết khóa là giả mạo được phiên đăng nhập của bất kỳ ai.
        """
        with without_env('DJANGO_SECRET_KEY'):
            with self.assertRaises(ImproperlyConfigured):
                _resolve_secret_key(debug=False)

    def test_the_error_says_which_variable_is_missing(self):
        with without_env('DJANGO_SECRET_KEY'):
            with self.assertRaises(ImproperlyConfigured) as caught:
                _resolve_secret_key(debug=False)
        self.assertIn('DJANGO_SECRET_KEY', str(caught.exception))

    def test_an_empty_variable_counts_as_missing(self):
        """Biến rỗng là lỗi cấu hình thường gặp hơn biến thiếu hẳn — `KEY=` trong `.env`,
        hoặc một ô để trống trên bảng điều khiển của Render."""
        with mock.patch.dict(os.environ, {'DJANGO_SECRET_KEY': ''}):
            with self.assertRaises(ImproperlyConfigured):
                _resolve_secret_key(debug=False)

    def test_a_whitespace_only_variable_counts_as_missing(self):
        with mock.patch.dict(os.environ, {'DJANGO_SECRET_KEY': '   '}):
            with self.assertRaises(ImproperlyConfigured):
                _resolve_secret_key(debug=False)

    def test_development_falls_back_instead_of_blocking_work(self):
        """Ở `DEBUG=True` thì vẫn phải chạy được ngay sau khi clone, không cần `.env`."""
        with without_env('DJANGO_SECRET_KEY'):
            self.assertEqual(_resolve_secret_key(debug=True), DEV_SECRET_KEY)

    def test_the_fallback_is_not_the_key_that_leaked(self):
        """Khóa cũ vẫn còn trong lịch sử git của repo public, nên nó **không được** tiếp
        tục làm giá trị dự phòng — kể cả cho môi trường dev."""
        self.assertNotIn('bab1(0x', DEV_SECRET_KEY)

    def test_the_fallback_says_out_loud_that_it_is_insecure(self):
        self.assertIn('insecure', DEV_SECRET_KEY)


class CookieFlagTests(SimpleTestCase):
    """Cờ `Secure` cho cookie phiên và cookie CSRF — [S-11](../../docs/SECURITY.md).

    Render phục vụ qua HTTPS, nhưng cookie không mang cờ `Secure` thì trình duyệt vẫn
    được phép gửi nó qua một kết nối HTTP thường nếu có đường nào dẫn tới đó.

    Không khẳng định giá trị đang chạy (nó phụ thuộc `.env` của máy) mà khẳng định
    **quy tắc**: hai cờ luôn là nghịch đảo của `DEBUG`.
    """

    def test_a_production_like_environment_gets_secure_cookies(self):
        with reloaded_settings(DJANGO_SECRET_KEY='khoa-that') as base:
            self.assertFalse(base.DEBUG)
            self.assertTrue(base.SESSION_COOKIE_SECURE)
            self.assertTrue(base.CSRF_COOKIE_SECURE)

    def test_a_development_environment_does_not(self):
        with reloaded_settings(DJANGO_DEBUG='1') as base:
            self.assertTrue(base.DEBUG)
            self.assertFalse(base.SESSION_COOKIE_SECURE)
            self.assertFalse(base.CSRF_COOKIE_SECURE)

    def test_the_test_settings_keep_them_off(self):
        """`settings_test` đặt tay cả hai thành `False` để test không phụ thuộc `.env`
        của máy đang chạy — `manage.py test` dùng `http://testserver`, không phải HTTPS."""
        from django.conf import settings

        self.assertFalse(settings.SESSION_COOKIE_SECURE)
        self.assertFalse(settings.CSRF_COOKIE_SECURE)
