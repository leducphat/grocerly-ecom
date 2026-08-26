"""Unit test cho `core/vnpay.py` — PLAN bước 2.6a.

VNPay là một trong hai điểm nhấn của đề tài, và là phần **tự implement** chứ không dùng
SDK: ký HMAC-SHA512 trên chuỗi tham số đã sort. Trước file này nó không có một test nào
(SPEC-GAPS C7).

Đây là unit test thật: `SimpleTestCase` nên **không tạo database**, và chữ ký kỳ vọng
được tính lại độc lập bằng `hmac`/`hashlib` thay vì gọi hàm băm của chính lớp `vnpay` —
nếu không thì test chỉ chứng minh code nhất quán với chính nó, không chứng minh nó đúng
thuật toán VNPay quy định.
"""

import hashlib
import hmac
import urllib.parse

from django.test import SimpleTestCase

from core.vnpay import vnpay


SECRET = "GROCERLY_TEST_SECRET"
PAY_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"


def signed_query(params):
    """Chuỗi ký theo đúng đặc tả VNPay: sort theo tên, bỏ giá trị rỗng, URL-encode.

    Viết tay ở đây có chủ ý — xem docstring đầu file.
    """
    parts = [
        f"{key}={urllib.parse.quote_plus(str(value))}"
        for key, value in sorted(params.items())
        if str(value).strip() != ''
    ]
    return "&".join(parts)


def expected_signature(params, secret=SECRET):
    return hmac.new(
        secret.encode('utf-8'),
        signed_query(params).encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()


def query_of(url):
    """Tách phần query của URL thành dict phẳng, giống cách Django dựng `request.GET`."""
    raw = urllib.parse.urlparse(url).query
    return {key: values[0] for key, values in urllib.parse.parse_qs(raw).items()}


class GetPaymentUrlTests(SimpleTestCase):
    """Dựng URL chuyển hướng sang cổng thanh toán."""

    def setUp(self):
        self.params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': 'GROCERLY',
            'vnp_Amount': '50000000',
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': '12345678-1700000000',
            'vnp_OrderInfo': 'Thanh toan don hang 12345678',
            'vnp_Locale': 'vn',
        }

    def _build(self, **overrides):
        params = dict(self.params)
        params.update(overrides)
        vnp = vnpay()
        vnp.requestData = params
        return vnp.get_payment_url(PAY_URL, SECRET), params

    def test_params_are_sorted_alphabetically(self):
        # VNPay ký trên chuỗi đã sort; sai thứ tự là sai chữ ký, dù dữ liệu đúng.
        url, _ = self._build()
        query = urllib.parse.urlparse(url).query
        names = [pair.split('=')[0] for pair in query.split('&')]
        signed_names = [name for name in names if name != 'vnp_SecureHash']

        self.assertEqual(signed_names, sorted(signed_names))

    def test_empty_values_are_left_out(self):
        url, _ = self._build(vnp_BankCode='')

        self.assertNotIn('vnp_BankCode', query_of(url))

    def test_values_are_url_encoded(self):
        url, _ = self._build()

        # quote_plus: dấu cách thành '+', không phải '%20'.
        self.assertIn('vnp_OrderInfo=Thanh+toan+don+hang+12345678', url)

    def test_signature_matches_an_independently_computed_hmac(self):
        url, params = self._build()

        self.assertEqual(query_of(url)['vnp_SecureHash'], expected_signature(params))

    def test_signature_covers_the_amount(self):
        """Đổi số tiền phải ra chữ ký khác — nếu không thì chữ ký vô nghĩa."""
        url_a, _ = self._build(vnp_Amount='50000000')
        url_b, _ = self._build(vnp_Amount='1')

        self.assertNotEqual(
            query_of(url_a)['vnp_SecureHash'],
            query_of(url_b)['vnp_SecureHash'],
        )

    def test_whitespace_around_the_secret_and_url_is_stripped(self):
        """Biến môi trường hay dính khoảng trắng/xuống dòng thừa khi copy-paste."""
        vnp = vnpay()
        vnp.requestData = dict(self.params)
        messy = vnp.get_payment_url(f"  {PAY_URL}\n", f"  {SECRET}\n")

        clean, _ = self._build()
        self.assertEqual(messy, clean)


class ValidateResponseTests(SimpleTestCase):
    """Kiểm chữ ký trên dữ liệu VNPay trả về — chốt chặn của `vnpay_return` và `vnpay_ipn`."""

    def setUp(self):
        self.params = {
            'vnp_Amount': '50000000',
            'vnp_ResponseCode': '00',
            'vnp_TxnRef': '12345678-1700000000',
            'vnp_TransactionNo': '14012345',
        }
        self.signature = expected_signature(self.params)

    def _validate(self, data, secret=SECRET):
        vnp = vnpay()
        vnp.responseData = dict(data)
        return vnp.validate_response(secret)

    def _signed(self, **overrides):
        data = dict(self.params, vnp_SecureHash=self.signature)
        data.update(overrides)
        return data

    def test_accepts_a_correct_signature(self):
        self.assertTrue(self._validate(self._signed()))

    def test_rejects_a_tampered_amount(self):
        # Kịch bản thật: sửa vnp_Amount trên URL trả về để "trả" ít hơn số đã đặt.
        self.assertFalse(self._validate(self._signed(vnp_Amount='1')))

    def test_rejects_a_tampered_response_code(self):
        # Đổi mã lỗi thành '00' để giả vờ thanh toán thành công.
        failed = dict(self.params, vnp_ResponseCode='24')
        data = dict(failed, vnp_SecureHash=expected_signature(failed))
        data['vnp_ResponseCode'] = '00'

        self.assertFalse(self._validate(data))

    def test_rejects_a_missing_signature(self):
        self.assertFalse(self._validate(self.params))

    def test_rejects_a_wrong_secret(self):
        self.assertFalse(self._validate(self._signed(), secret="SAI_SECRET"))

    def test_hash_type_field_is_not_part_of_the_signed_string(self):
        # vnp_SecureHashType đi kèm chữ ký nhưng không được ký cùng.
        self.assertTrue(self._validate(self._signed(vnp_SecureHashType='SHA512')))

    def test_params_without_the_vnp_prefix_are_ignored(self):
        # Chỉ tham số 'vnp_*' tham gia chuỗi ký, nên rác thêm vào không phá được chữ ký.
        self.assertTrue(self._validate(self._signed(utm_source='facebook')))

    def test_empty_vnp_params_are_left_out_of_the_signed_string(self):
        self.assertTrue(self._validate(self._signed(vnp_BankCode='')))

    def test_signature_comparison_ignores_case(self):
        """Chữ ký viết HOA vẫn phải được chấp nhận.

        Cổng sandbox đang dùng trả chữ thường nên trước khi sửa cũng không có gì hỏng.
        Nhưng đặc tả VNPay không cam kết chữ thường, nên đây là rủi ro của lúc **chuyển
        sang cổng thật**: nếu cổng trả chữ HOA thì mọi giao dịch thành công đều bị coi là
        sai chữ ký và rơi vào `payment-failed`, hỏng im lặng.
        """
        self.assertTrue(self._validate(self._signed(vnp_SecureHash=self.signature.upper())))

    def test_a_wrong_signature_is_still_rejected_in_either_case(self):
        """Bỏ phân biệt hoa thường không được nới lỏng việc kiểm chữ ký."""
        wrong = 'a' * 128

        self.assertFalse(self._validate(self._signed(vnp_SecureHash=wrong)))
        self.assertFalse(self._validate(self._signed(vnp_SecureHash=wrong.upper())))

    def test_validating_does_not_modify_the_data_passed_in(self):
        """`validate_response` không được sửa `responseData` của chính nó.

        Trước đây nó `pop` thẳng `vnp_SecureHash` ra khỏi dict, nên gọi lần hai trên cùng
        một object luôn trả False. Không ai trúng bẫy vì `vnpay_return`/`vnpay_ipn` mỗi
        lần đều tạo object mới — nhưng một hàm *kiểm tra* thì không nên có tác dụng phụ.
        """
        vnp = vnpay()
        vnp.responseData = self._signed()
        before = dict(vnp.responseData)

        self.assertTrue(vnp.validate_response(SECRET))
        self.assertEqual(vnp.responseData, before)
        # Gọi lại vẫn cho cùng kết quả — đây mới là điều đáng tin ở một hàm kiểm tra.
        self.assertTrue(vnp.validate_response(SECRET))


class RoundTripTests(SimpleTestCase):
    """Đi trọn vòng: URL do ta dựng → trình duyệt giải mã → ta kiểm lại chữ ký.

    Đây là test có giá trị nhất trong file: `get_payment_url` mã hóa bằng `quote_plus`,
    trình duyệt/Django giải mã khi dựng `request.GET`, rồi `validate_response` mã hóa
    lại. Ba bước đó phải khớp nhau tuyệt đối, và không test đơn lẻ nào phát hiện được
    nếu một bước lệch.
    """

    def test_url_built_here_validates_after_a_browser_round_trip(self):
        vnp = vnpay()
        vnp.requestData = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_Amount': '50000000',
            'vnp_OrderInfo': 'Thanh toan don hang 12345678',
            'vnp_TxnRef': '12345678-1700000000',
            'vnp_Locale': '',
        }
        url = vnp.get_payment_url(PAY_URL, SECRET)

        returned = vnpay()
        returned.responseData = query_of(url)

        self.assertTrue(returned.validate_response(SECRET))
