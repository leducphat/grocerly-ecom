"""Unit test cho các helper nằm trên đường tiền — PLAN bước 2.6b và 2.6c.

Bốn hàm ở đây quyết định **khách trả bao nhiêu** và **khách nhìn thấy con số nào**:

- `safe_float` / `safe_int` (`core/views.py`) đọc giá và số lượng ra khỏi session giỏ
  hàng, rồi kết quả đi thẳng vào `CartOrder.price` và `CartOrderItem.price`
- `vnd` / `mul` (`core/templatetags/currency_filters.py`) render mọi con số tiền trên
  **mọi** trang có giá

`SimpleTestCase` — không hàm nào chạm database, nên không dựng database.

Đọc thêm: bước 2.6b trong [PLAN.md](../../docs/PLAN.md) ghi lại lần dò đầu tiên, khi
`safe_float` còn trả `0.0` cho định dạng tiền Việt có phần thập phân. Các test đánh dấu
`# 2.6b` bên dưới là những chỗ hành vi cũ **sai** và đã được sửa cùng lô này.
"""

from decimal import Decimal

from django.test import SimpleTestCase

from core.templatetags.currency_filters import mul, vnd
from core.views import safe_float, safe_int


class SafeFloatVietnameseMoneyTests(SimpleTestCase):
    """Định dạng tiền Việt — dấu chấm phân nhóm nghìn, dấu phẩy ngăn thập phân."""

    def test_reads_a_dot_grouped_amount_without_decimals(self):
        self.assertEqual(safe_float('1.000.000'), 1000000.0)

    def test_reads_a_dot_grouped_amount_with_decimals(self):
        # 2.6b — trước đây trả 0.0. Regex phân nhóm cũ neo `$` ở cuối chuỗi nên phần
        # `,50` làm nó trượt, dấu chấm ở lại, rồi `float('1.000.000.50')` ném ValueError.
        self.assertEqual(safe_float('1.000.000,50'), 1000000.5)

    def test_reads_a_bare_decimal_comma(self):
        self.assertEqual(safe_float('12,5'), 12.5)

    def test_treats_a_lone_three_digit_group_as_thousands_not_decimals(self):
        """`50.000` là năm mươi nghìn đồng, không phải năm mươi phẩy không."""
        self.assertEqual(safe_float('50.000'), 50000.0)

    def test_strips_the_dong_sign(self):
        self.assertEqual(safe_float('50000₫'), 50000.0)

    def test_strips_a_trailing_vnd_label(self):
        self.assertEqual(safe_float('50.000 VND'), 50000.0)

    def test_reads_an_amount_grouped_with_spaces(self):
        self.assertEqual(safe_float('1 000 000'), 1000000.0)


class SafeFloatEnglishMoneyTests(SimpleTestCase):
    """Định dạng Anh–Mỹ — dấu phẩy phân nhóm, dấu chấm ngăn thập phân."""

    def test_reads_a_comma_grouped_amount(self):
        self.assertEqual(safe_float('1,234,567'), 1234567.0)

    def test_reads_a_comma_grouped_amount_with_decimals(self):
        # 2.6b — trước đây trả 0.0, cùng nguyên nhân với bản tiếng Việt ở trên.
        self.assertEqual(safe_float('1,234.56'), 1234.56)

    def test_reads_a_bare_decimal_point(self):
        self.assertEqual(safe_float('12.99'), 12.99)

    def test_strips_the_dollar_sign(self):
        self.assertEqual(safe_float('$12.99'), 12.99)


class SafeFloatNumericInputTests(SimpleTestCase):
    """Giá trong session **luôn** là `float` đọc từ database, không phải chuỗi.

    `add_to_cart` ghi `'price': float(product.price)` (bản vá S-02). Đây mới là đường
    thật sự chạy trong production; nhánh phân tích chuỗi chỉ còn phục vụ dữ liệu cũ.
    """

    def test_passes_a_float_through_untouched(self):
        self.assertEqual(safe_float(12.99), 12.99)

    def test_passes_an_int_through_untouched(self):
        self.assertEqual(safe_float(50000), 50000.0)

    def test_reads_a_decimal_without_going_through_str(self):
        self.assertEqual(safe_float(Decimal('50000.50')), 50000.5)

    def test_keeps_a_price_large_enough_to_print_in_scientific_notation(self):
        """2.6b — `Product.price` là `DecimalField(max_digits=20)` nên giá trị này
        **nằm trong tầm hợp lệ** của model, không phải trường hợp giả định.

        Trước đây `str(1e16)` cho `'1e+16'`, rồi bước lọc ký tự vứt `e` và `+` đi, còn
        lại `'116'`. Đơn 10 triệu tỉ đồng bị tính thành 116 đồng.
        """
        self.assertEqual(safe_float(1e16), 1e16)

    def test_keeps_a_price_small_enough_to_print_in_scientific_notation(self):
        """Chiều ngược lại còn nguy hiểm hơn: `str(0.00001)` cho `'1e-05'` → `'105'`,
        tức giá bị **thổi lên** mười triệu lần chứ không phải giảm đi."""
        self.assertEqual(safe_float(0.00001), 0.00001)


class SafeFloatSignTests(SimpleTestCase):
    """Dấu âm phải được giữ.

    Không phải để hỗ trợ giá âm — mà để hàm **không nói dối**. Bước lọc ký tự cũ vứt dấu
    trừ đi, nên `-5` thành `5.0`: một khoản trừ biến thành một khoản cộng, im lặng.
    """

    def test_keeps_a_negative_integer_negative(self):
        # 2.6b — trước đây trả 5.0.
        self.assertEqual(safe_float('-5'), -5.0)

    def test_keeps_a_negative_decimal_negative(self):
        # 2.6b — trước đây trả 5.5.
        self.assertEqual(safe_float('-5.5'), -5.5)

    def test_keeps_a_negative_float_negative(self):
        self.assertEqual(safe_float(-5.5), -5.5)

    def test_accepts_an_explicit_plus_sign(self):
        self.assertEqual(safe_float('+5'), 5.0)


class SafeFloatFallbackTests(SimpleTestCase):
    """Đầu vào không đọc được phải rơi về `default`, **không** thành một con số bịa ra.

    Đây là chỗ đáng ngại nhất của bản cũ: nó lọc bỏ mọi ký tự lạ rồi tính trên phần còn
    lại, nên rác vẫn cho ra một con số trông hợp lệ.
    """

    def test_none_falls_back(self):
        self.assertEqual(safe_float(None), 0.0)

    def test_empty_string_falls_back(self):
        self.assertEqual(safe_float(''), 0.0)

    def test_blank_string_falls_back(self):
        self.assertEqual(safe_float('   '), 0.0)

    def test_letters_fall_back(self):
        self.assertEqual(safe_float('abc'), 0.0)

    def test_a_malformed_group_falls_back(self):
        """`1.5.5` không phải số nào cả — nhóm nghìn phải đúng ba chữ số."""
        self.assertEqual(safe_float('1.5.5'), 0.0)

    def test_a_list_falls_back_instead_of_becoming_its_contents(self):
        # 2.6b — `str([1])` là `'[1]'`, bước lọc cũ giữ lại `'1'` rồi trả 1.0.
        self.assertEqual(safe_float([1]), 0.0)

    def test_a_dict_falls_back_instead_of_becoming_its_contents(self):
        # 2.6b — `str({'a': 1})` cũng lọc ra `'1'` theo đúng cách đó.
        self.assertEqual(safe_float({'a': 1}), 0.0)

    def test_the_caller_can_choose_the_fallback(self):
        self.assertEqual(safe_float('abc', default=7.5), 7.5)

    def test_a_lone_separator_falls_back(self):
        self.assertEqual(safe_float('.'), 0.0)


class SafeIntTests(SimpleTestCase):
    """`safe_int` phục vụ **số lượng**, nên `default` là 1 chứ không phải 0."""

    def test_reads_a_plain_integer(self):
        self.assertEqual(safe_int('3'), 3)

    def test_truncates_toward_zero_rather_than_rounding(self):
        self.assertEqual(safe_int('3.7'), 3)

    def test_reads_a_grouped_amount(self):
        self.assertEqual(safe_int('1.000.000'), 1000000)

    def test_missing_quantity_defaults_to_one(self):
        """Giỏ hàng không có món nào với số lượng 0, nên thiếu dữ liệu nghĩa là 1."""
        self.assertEqual(safe_int(None), 1)

    def test_unreadable_quantity_defaults_to_one(self):
        self.assertEqual(safe_int('abc'), 1)

    def test_an_explicit_zero_stays_zero(self):
        """Khác với thiếu dữ liệu: `'0'` là con số khách gửi lên, phải đọc đúng.

        `add_to_cart` và `update_cart` đều bọc kết quả trong `max(1, ...)`, nên việc kẹp
        cận dưới là trách nhiệm của view — không phải của helper này.
        """
        self.assertEqual(safe_int('0'), 0)

    def test_the_caller_can_choose_the_fallback(self):
        self.assertEqual(safe_int('abc', default=0), 0)

    def test_keeps_a_negative_quantity_negative(self):
        # 2.6b — trước đây trả 5, tức một số âm lọt qua thành số dương.
        self.assertEqual(safe_int('-5'), -5)


class VndFilterTests(SimpleTestCase):
    """`{{ value|vnd }}` — dấu chấm phân nhóm nghìn, không phần thập phân, không ký hiệu.

    Ký hiệu `₫` do template tự thêm sau filter, nên filter chỉ trả về phần chữ số.
    """

    def test_groups_thousands_with_dots(self):
        self.assertEqual(vnd(1234567), '1.234.567')

    def test_leaves_a_short_number_ungrouped(self):
        self.assertEqual(vnd(999), '999')

    def test_rounds_half_up_rather_than_to_even(self):
        """`ROUND_HALF_UP` là quy ước làm tròn tiền của người dùng.

        Mặc định của Python là `ROUND_HALF_EVEN`, cho 0 ở đây — đúng chuẩn IEEE nhưng
        không phải cái khách hàng trông đợi khi nhìn hóa đơn.
        """
        self.assertEqual(vnd(Decimal('0.5')), '1')

    def test_rounds_half_up_away_from_zero_on_a_larger_amount(self):
        self.assertEqual(vnd(Decimal('1234.5')), '1.235')

    def test_rounds_down_below_the_halfway_point(self):
        self.assertEqual(vnd(Decimal('1234.4')), '1.234')

    def test_reads_a_decimal_exactly(self):
        self.assertEqual(vnd(Decimal('1000000.00')), '1.000.000')

    def test_reads_a_numeric_string(self):
        self.assertEqual(vnd('1234567'), '1.234.567')

    def test_keeps_the_minus_sign_outside_the_grouping(self):
        self.assertEqual(vnd(Decimal('-1234567')), '-1.234.567')

    def test_none_renders_as_zero(self):
        """Trang phải hiện `0` chứ không được vỡ: giá `NULL` là chuyện có thật trong
        database này (xem `core/test_missing_relations.py`)."""
        self.assertEqual(vnd(None), '0')

    def test_an_unreadable_value_renders_as_zero(self):
        self.assertEqual(vnd('abc'), '0')

    def test_zero_renders_as_zero(self):
        self.assertEqual(vnd(0), '0')


class MulFilterTests(SimpleTestCase):
    """`{{ price|mul:qty }}` — nhân bằng `Decimal` để không sinh sai số nhị phân.

    Đây là lý do filter tồn tại thay vì tính trong view: `0.1 * 3` bằng float cho
    `0.30000000000000004`, và con số đó từng hiện ra trên trang giỏ hàng.
    """

    def test_multiplies_two_integers(self):
        self.assertEqual(mul(1000, 3), Decimal('3000'))

    def test_multiplies_without_binary_rounding_error(self):
        self.assertEqual(mul('0.1', 3), Decimal('0.3'))

    def test_multiplies_a_decimal_by_a_string(self):
        self.assertEqual(mul(Decimal('12000.50'), '2'), Decimal('24001.00'))

    def test_a_none_operand_makes_the_product_zero(self):
        self.assertEqual(mul(None, 3), Decimal('0'))

    def test_an_unreadable_operand_makes_the_product_zero(self):
        self.assertEqual(mul('abc', 3), Decimal('0'))

    def test_the_result_feeds_back_into_vnd(self):
        """Hai filter luôn đi cặp trong template: `{{ p.price|mul:p.qty|vnd }}`."""
        self.assertEqual(vnd(mul('12500.50', 4)), '50.002')
