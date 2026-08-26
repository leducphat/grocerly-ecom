"""Form liên hệ — vá lỗ ghi database bằng GET không xác thực.

`ajax_contact_form` từng là view GET, không đăng nhập, không kiểm gì, ghi thẳng
`ContactUs.objects.create()` từ query string. Vì **không cần cookie**, chính sách
SameSite của trình duyệt không đỡ được: mọi trang bên ngoài chỉ cần nhúng

    <img src="https://.../vi/ajax-contact-form/?full_name=x&...&message=<rác>">

là mỗi lượt xem trang của họ tạo một dòng trên database production. `message` là
TextField không giới hạn nên còn là đường làm phình storage.

Phát hiện trong lượt rà soát các endpoint thay đổi trạng thái, 2026-08-26.
"""

from django.test import Client, TestCase
from django.urls import reverse

from userauths.models import ContactUs


VALID = {
    'full_name': "Lê Văn A",
    'email': "levana@example.com",
    'phone': "0900000000",
    'subject': "Hỏi về đơn hàng",
    'message': "Đơn của tôi bao giờ giao?",
}


class ContactFormWritePathTests(TestCase):
    """Chỉ POST kèm token CSRF mới ghi được."""

    def _post(self, **overrides):
        data = dict(VALID)
        data.update(overrides)
        return self.client.post(reverse("core:ajax-contact-form"), data)

    def test_a_valid_post_creates_the_message(self):
        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['bool'])
        self.assertEqual(ContactUs.objects.count(), 1)
        self.assertEqual(ContactUs.objects.get().full_name, "Lê Văn A")

    def test_a_get_writes_nothing(self):
        """Chính là vector <img src>. GET không bị CSRF middleware kiểm token."""
        response = self.client.get(reverse("core:ajax-contact-form"), VALID)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(ContactUs.objects.count(), 0)

    def test_a_post_without_a_csrf_token_writes_nothing(self):
        strict = Client(enforce_csrf_checks=True)

        response = strict.post(reverse("core:ajax-contact-form"), VALID)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(ContactUs.objects.count(), 0)


class ContactFormValidationTests(TestCase):
    """Trường rỗng từng gây 500; `message` từng không có trần độ dài."""

    def _post(self, **overrides):
        data = dict(VALID)
        data.update(overrides)
        return self.client.post(reverse("core:ajax-contact-form"), data)

    def test_a_missing_field_is_rejected_instead_of_crashing(self):
        # Mọi field của ContactUs đều NOT NULL và `create()` không gọi `full_clean()`,
        # nên trước đây thiếu tham số là IntegrityError → lỗi 500.
        response = self._post(full_name="")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactUs.objects.count(), 0)

    def test_whitespace_only_counts_as_missing(self):
        response = self._post(subject="   ")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactUs.objects.count(), 0)

    def test_an_overlong_message_is_rejected(self):
        """Trần này là thứ duy nhất chặn việc nhồi dòng khổng lồ — model là TextField."""
        response = self._post(message="x" * 2001)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactUs.objects.count(), 0)

    def test_a_message_at_the_limit_is_accepted(self):
        response = self._post(message="x" * 2000)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactUs.objects.count(), 1)

    def test_an_overlong_short_field_is_rejected(self):
        """Vượt max_length của model thì PostgreSQL ném lỗi, SQLite thì âm thầm cắt."""
        response = self._post(subject="x" * 201)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactUs.objects.count(), 0)

    def test_a_malformed_email_is_rejected(self):
        # `ContactUs.email` là CharField chứ không phải EmailField, nên model không kiểm
        # định dạng — phải kiểm ở view.
        response = self._post(email="khong-phai-email")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactUs.objects.count(), 0)

    def test_the_error_body_is_readable_by_the_contact_widget(self):
        """JS đọc `xhr.responseJSON.error`; thiếu khóa này là lỗi bị nuốt im lặng."""
        response = self._post(email="khong-phai-email")

        self.assertIn('error', response.json())
        self.assertTrue(response.json()['error'])


class ContactFormTemplateTests(TestCase):
    """Chốt luôn phía giao diện: JS phải gửi POST kèm token."""

    def test_the_contact_page_posts_with_a_csrf_token(self):
        response = self.client.get(reverse("core:contact"))
        html = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertIn('"csrfmiddlewaretoken": getCookie("csrftoken")', html)
        self.assertNotIn('type: "GET"', html.split("Contact Form AJAX")[1][:900])
