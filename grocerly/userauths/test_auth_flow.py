"""Test cho luồng đăng ký / đăng nhập / đăng xuất — PLAN bước 2.6g.

Trước file này `userauths/tests.py` là stub rỗng ba dòng: **app quản lý tài khoản của dự
án không có một test nào**, dù nó quyết định ai là khách, ai là nhân viên, và mỗi vai trò
hạ cánh ở trang nào sau khi đăng nhập.

Ba chỗ đáng chú ý khi đọc file này:

- `User.USERNAME_FIELD` là `email`, không phải `username`. `username` vẫn tồn tại nhưng
  **không unique** — chỉ là tên hiển thị.
- `Profile` được tạo bằng signal `post_save`, không phải trong view. Đăng ký hỏng mà
  profile vẫn sinh ra (hoặc ngược lại) là lỗi không view nào bắt được.
- Điều hướng sau đăng nhập rẽ ba nhánh theo vai trò, và nhánh nhân viên trùng ý đồ với
  `RestrictStaffMiddleware` (**bẫy #6**) — xem `core/test_middleware.py`.
"""

from unittest import mock

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from userauths.models import Profile, User


PASSWORD = 'grocerly-test-pw-9137'


def messages_in(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class RegisterTests(TestCase):
    """Đăng ký tài khoản khách hàng."""

    URL = reverse('userauths:sign-up')

    def valid_payload(self, **overrides):
        payload = {
            'email': 'khach@grocerly.test',
            'username': 'khach',
            'password1': PASSWORD,
            'password2': PASSWORD,
        }
        payload.update(overrides)
        return payload

    def test_the_form_renders(self):
        self.assertEqual(self.client.get(self.URL).status_code, 200)

    def test_a_valid_submission_creates_the_account(self):
        self.client.post(self.URL, self.valid_payload())
        self.assertTrue(User.objects.filter(email='khach@grocerly.test').exists())

    def test_a_valid_submission_signs_the_new_user_in(self):
        """Đăng ký xong là vào thẳng, không bắt đăng nhập lại."""
        response = self.client.post(self.URL, self.valid_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:index'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_the_signal_creates_a_profile_alongside_the_user(self):
        """`Profile` do signal `post_save` sinh ra, không phải view — nên nếu ai đó bỏ
        signal đi thì đăng ký vẫn "thành công" và chỉ vỡ ở trang sửa hồ sơ."""
        self.client.post(self.URL, self.valid_payload())
        user = User.objects.get(email='khach@grocerly.test')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_a_new_account_is_a_customer_not_staff(self):
        """Nếu điều này sai thì người vừa đăng ký sẽ bị `RestrictStaffMiddleware` đá
        thẳng vào trang quản trị — vừa hỏng luồng mua hàng, vừa là lỗ hổng phân quyền."""
        self.client.post(self.URL, self.valid_payload())
        user = User.objects.get(email='khach@grocerly.test')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_a_duplicate_email_is_rejected(self):
        User.objects.create_user(
            email='khach@grocerly.test', username='nguoi-khac', password=PASSWORD,
        )
        response = self.client.post(self.URL, self.valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email='khach@grocerly.test').count(), 1)

    def test_mismatched_passwords_are_rejected(self):
        response = self.client.post(
            self.URL, self.valid_payload(password2=PASSWORD + '-khac'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='khach@grocerly.test').exists())

    def test_the_sign_up_form_rejects_a_duplicate_username(self):
        """Form chặn trùng `username`, dù **model không hề bắt buộc** điều đó.

        `userauths.User` khai đè `username` thành `CharField` thường (bỏ `unique=True`
        của `AbstractUser`), vì định danh đăng nhập là email. Nhưng `UserCreationForm`
        của Django mang sẵn `clean_username` từ chối tên đã tồn tại — không phân biệt
        hoa thường — nên đường đăng ký vẫn chặt hơn database.

        Hai mức khác nhau, và test dưới ghi lại mức còn lại.
        """
        User.objects.create_user(
            email='nguoikhac@grocerly.test', username='khach', password=PASSWORD,
        )
        response = self.client.post(self.URL, self.valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='khach@grocerly.test').exists())

    def test_the_database_itself_still_allows_duplicate_usernames(self):
        """Chốt chặn trên **chỉ nằm ở form**, không nằm ở model.

        Nghĩa là mọi đường tạo tài khoản khác — `createsuperuser`, Django Admin, shell,
        fixture — đều tạo được hai người trùng tên. Đừng viết code nào coi `username` là
        khóa: `User.objects.get(username=...)` sẽ ném `MultipleObjectsReturned`.
        """
        User.objects.create_user(
            email='mot@grocerly.test', username='trung-ten', password=PASSWORD,
        )
        User.objects.create_user(
            email='hai@grocerly.test', username='trung-ten', password=PASSWORD,
        )
        self.assertEqual(User.objects.filter(username='trung-ten').count(), 2)


class LoginRedirectByRoleTests(TestCase):
    """Đăng nhập đúng thông tin — mỗi vai trò hạ cánh ở một trang khác nhau."""

    URL = reverse('userauths:sign-in')

    def setUp(self):
        self.customer = User.objects.create_user(
            email='khach@grocerly.test', username='khach', password=PASSWORD,
        )

    def sign_in(self, email):
        return self.client.post(self.URL, {'email': email, 'password': PASSWORD})

    def test_a_customer_lands_on_the_storefront(self):
        response = self.sign_in(self.customer.email)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:index'))

    def test_a_staff_member_lands_on_the_dashboard(self):
        self.customer.is_staff = True
        self.customer.save()
        response = self.sign_in(self.customer.email)
        self.assertEqual(response.url, reverse('useradmin:dashboard'))

    def test_a_superuser_lands_on_django_admin(self):
        self.customer.is_superuser = True
        self.customer.is_staff = True
        self.customer.save()
        response = self.sign_in(self.customer.email)
        self.assertEqual(response.url, '/admin/')

    def test_signing_in_actually_starts_a_session(self):
        self.sign_in(self.customer.email)
        self.assertIn('_auth_user_id', self.client.session)

    def test_the_email_is_the_credential_not_the_username(self):
        """`USERNAME_FIELD = 'email'`: gõ tên hiển thị vào ô email là **không** vào được."""
        response = self.client.post(
            self.URL, {'email': 'khach', 'password': PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class LoginFailureTests(TestCase):
    """Đăng nhập sai — không được tạo phiên, và phải nói cho người dùng biết."""

    URL = reverse('userauths:sign-in')

    def setUp(self):
        self.customer = User.objects.create_user(
            email='khach@grocerly.test', username='khach', password=PASSWORD,
        )

    def test_a_wrong_password_does_not_start_a_session(self):
        response = self.client.post(
            self.URL, {'email': self.customer.email, 'password': 'sai-mat-khau'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_a_wrong_password_says_so(self):
        response = self.client.post(
            self.URL, {'email': self.customer.email, 'password': 'sai-mat-khau'},
        )
        self.assertTrue(messages_in(response))

    def test_an_unknown_email_does_not_start_a_session(self):
        """Test khẳng định **kết quả** (không có phiên, có thông báo) chứ không khẳng
        định cách bắt lỗi.

        Nhờ vậy nó xanh cả trước lẫn sau bản vá [S-07](../../docs/SECURITY.md), vốn bỏ
        hẳn khối `try`/`except:` trần ở view này. Đó là chủ ý: lưới an toàn cho bản vá,
        chứ không phải cái chốt lại hành vi sai. Phần khẳng định điều S-07 thật sự đổi
        nằm ở `LoginErrorHandlingTests`.
        """
        response = self.client.post(
            self.URL, {'email': 'khongtontai@grocerly.test', 'password': PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertTrue(messages_in(response))

    def test_an_empty_submission_does_not_crash(self):
        response = self.client.post(self.URL, {})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class LoginErrorHandlingTests(TestCase):
    """[S-07](../../docs/SECURITY.md) — lỗi thật không được hóa trang thành lỗi nhập liệu."""

    URL = reverse('userauths:sign-in')

    def setUp(self):
        self.customer = User.objects.create_user(
            email='khach@grocerly.test', username='khach', password=PASSWORD,
        )

    def test_an_unexpected_error_is_not_swallowed(self):
        """Trước bản vá, `except:` trần ở đây bắt **mọi** exception — kể cả lỗi kết nối
        database — rồi báo cho khách rằng email không tồn tại.

        Sự cố thật bị nuốt, không log, không dấu vết. Đúng lúc demo mà database chập
        chờn thì màn hình nói sai hoàn toàn về nguyên nhân.
        """
        with mock.patch('userauths.views.authenticate', side_effect=RuntimeError('db down')):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    self.URL, {'email': self.customer.email, 'password': PASSWORD},
                )

    def test_the_message_is_the_same_whether_or_not_the_email_exists(self):
        """Hai thông điệp khác nhau cho hai trường hợp là một **oracle liệt kê tài khoản**.

        Bản cũ trả "User does not exist" khi sai mật khẩu, nhưng "User with email X does
        not exist" khi email chưa đăng ký — đủ để dò xem một địa chỉ có tài khoản ở đây
        hay không, mà không cần đoán trúng mật khẩu.
        """
        wrong_password = self.client.post(
            self.URL, {'email': self.customer.email, 'password': 'sai-mat-khau'},
        )
        unknown_email = self.client.post(
            self.URL, {'email': 'khongtontai@grocerly.test', 'password': PASSWORD},
        )
        self.assertEqual(messages_in(wrong_password), messages_in(unknown_email))

    def test_the_message_does_not_echo_the_submitted_email(self):
        """Chuỗi cũ nhét thẳng `email` từ POST vào thông điệp rồi đẩy ra template."""
        response = self.client.post(
            self.URL, {'email': 'khongtontai@grocerly.test', 'password': PASSWORD},
        )
        for message in messages_in(response):
            self.assertNotIn('khongtontai@grocerly.test', message)


class AlreadySignedInTests(TestCase):
    """Đã đăng nhập rồi mà mở lại trang đăng nhập."""

    URL = reverse('userauths:sign-in')

    def setUp(self):
        self.customer = User.objects.create_user(
            email='khach@grocerly.test', username='khach', password=PASSWORD,
        )

    def test_a_customer_is_sent_to_the_storefront(self):
        self.client.force_login(self.customer)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:index'))

    def test_a_staff_member_is_sent_to_the_dashboard(self):
        self.customer.is_staff = True
        self.customer.save()
        self.client.force_login(self.customer)
        self.assertEqual(
            self.client.get(self.URL).url, reverse('useradmin:dashboard'),
        )

    def test_the_existing_session_survives(self):
        """Mở lại trang đăng nhập **không** được đá người ta ra."""
        self.client.force_login(self.customer)
        self.client.get(self.URL)
        self.assertIn('_auth_user_id', self.client.session)


class LogoutTests(TestCase):
    """Đăng xuất.

    POST, không GET — [S-10](../../docs/SECURITY.md), PLAN bước 2.14. Phần khẳng định
    rằng GET **không** còn đăng xuất được nằm ở `core/test_state_changing_methods.py`;
    ở đây chỉ kiểm hành vi bình thường.
    """

    URL = reverse('userauths:sign-out')

    def setUp(self):
        self.customer = User.objects.create_user(
            email='khach@grocerly.test', username='khach', password=PASSWORD,
        )

    def test_it_ends_the_session(self):
        self.client.force_login(self.customer)
        self.client.post(self.URL)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_it_sends_the_visitor_back_to_the_sign_in_page(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('userauths:sign-in'))

    def test_signing_out_while_already_signed_out_is_harmless(self):
        response = self.client.post(self.URL)
        self.assertEqual(response.status_code, 302)

    def test_staff_can_reach_the_sign_out_url(self):
        """`RestrictStaffMiddleware` chặn nhân viên khỏi mọi URL ngoài danh sách cho
        phép. Thiếu tiền tố sign-out trong danh sách đó là nhân viên **kẹt vĩnh viễn**
        trong phiên đăng nhập — xem `core/test_middleware.py`."""
        self.customer.is_staff = True
        self.customer.save()
        self.client.force_login(self.customer)
        self.client.post(self.URL)
        self.assertNotIn('_auth_user_id', self.client.session)


class ProfileUpdateAccessTests(TestCase):
    """Sửa hồ sơ — chỉ để kiểm chốt đăng nhập, không kiểm nội dung form."""

    URL = reverse('userauths:profile-update')

    def test_an_anonymous_visitor_is_sent_to_sign_in(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('userauths:sign-in').split('/user/')[0], response.url)

    def test_a_signed_in_customer_reaches_the_form(self):
        customer = User.objects.create_user(
            email='khach@grocerly.test', username='khach', password=PASSWORD,
        )
        self.client.force_login(customer)
        self.assertEqual(self.client.get(self.URL).status_code, 200)
