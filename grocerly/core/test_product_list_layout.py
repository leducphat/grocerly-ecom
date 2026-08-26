"""Cấu trúc HTML của trang danh sách sản phẩm — PLAN bước 2.8.

Trang `/products/` có một vùng bị JavaScript **ghi đè nguyên khối** mỗi khi khách đổi
bộ lọc:

    $("#filtered-product-grid").html(response.data);

Cái gì nằm trong vùng đó thì biến mất ngay lần tick checkbox đầu tiên. Đây từng là lỗi
thật: thẻ `<div id="filtered-product-grid">` **không được đóng**, nên vùng ghi đè kéo dài
tới hết mục "Deals Of The Day" và nuốt luôn mục đó.

Loại lỗi này **Django test client không nhìn thấy** theo cách thông thường — nó chỉ kiểm
HTML server trả về, mà HTML đó vẫn chứa đủ mọi thứ. Chỉ khi chạy JS trên trình duyệt thì
mục Deals mới bốc hơi. Nên các test dưới đây tự **đếm cân bằng thẻ `<div>`** để suy ra
biên thật của vùng ghi đè, thay vì chỉ kiểm "trang có chứa chuỗi X không".

Cũng chính vì thế mà thanh phân trang của bước 2.8 phải nằm **ngoài** vùng này.
"""

import re

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from core.models import Category, Product, Vendor


DIV_OPEN = re.compile(r'<div\b', re.I)
DIV_CLOSE = re.compile(r'</div\s*>', re.I)


def block_owned_by(html, element_id):
    """Trả về đoạn HTML nằm bên trong thẻ `<div id="...">`, tính theo cân bằng thẻ.

    Đây là điều mà `assertContains` không làm được: nó chỉ biết chuỗi có xuất hiện trên
    trang hay không, chứ không biết chuỗi đó nằm **trong hay ngoài** vùng bị ghi đè.
    """
    anchor = html.index(f'id="{element_id}"')
    start = html.rindex('<div', 0, anchor)

    depth = 0
    for match in re.finditer(r'<div\b|</div\s*>', html[start:], re.I):
        depth += 1 if match.group(0).lower().startswith('<div') else -1
        if depth == 0:
            return html[start:start + match.end()]
    raise AssertionError(f'Thẻ <div id="{element_id}"> không bao giờ được đóng')


class ProductListLayoutTests(TestCase):

    def setUp(self):
        category = Category.objects.create(title="Trái cây")
        vendor = Vendor.objects.create(name="Vinamilk")
        for i in range(3):
            Product.objects.create(
                title=f"Dưa hấu {i}", price=Decimal("50000.00"),
                product_status='published', category=category, vendor=vendor,
                featured=True,
            )

    def _html(self):
        response = self.client.get(reverse("core:product-list"))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_the_ajax_grid_is_actually_closed(self):
        """Thẻ không đóng là gốc rễ của mọi thứ còn lại trong file này."""
        block_owned_by(self._html(), "filtered-product-grid")   # ném nếu không đóng

    def test_the_deals_section_is_outside_the_ajax_grid(self):
        """Lỗi thật: lọc sản phẩm làm mất luôn mục "Deals Of The Day".

        Dịch tiêu đề qua `gettext` đúng cách template làm, thay vì khóa cứng tiếng Anh:
        ngôn ngữ mặc định của dự án là tiếng Việt nên trang render ra "Khuyến mãi trong
        ngày". Khóa cứng là test đỏ vì lý do không liên quan tới cái đang kiểm.
        """
        deals_title = _("Deals Of The Day")
        html = self._html()
        self.assertIn(deals_title, html)

        grid = block_owned_by(html, "filtered-product-grid")

        self.assertNotIn(deals_title, grid)

    def test_the_ajax_grid_holds_nothing_but_the_product_cards(self):
        """Chốt biên của vùng ghi đè: nó chỉ được chứa lưới sản phẩm.

        Sidebar bộ lọc và tiêu đề trang nằm ngoài — nếu lọt vào thì tick checkbox xong
        là chính cái checkbox đó biến mất.
        """
        grid = block_owned_by(self._html(), "filtered-product-grid")

        self.assertNotIn('shop-filter-toogle', grid)
        self.assertNotIn('id="slider-range"', grid)

    def test_the_pagination_bar_is_outside_the_ajax_grid(self):
        """Bất biến mà ba chỗ trong code trỏ về file này làm bằng chứng — nhưng trước đó
        không test nào chốt nó.

        Thanh phân trang nằm trong vùng bị ghi đè thì nó biến mất ngay lần khách tick
        checkbox đầu tiên, và `filter_product` trả `pagination` về một phần tử không còn
        tồn tại.
        """
        for i in range(20):     # đủ nhiều để thanh phân trang thật sự hiện ra
            Product.objects.create(
                title=f"Xoài {i}", price=Decimal("70000.00"), product_status='published',
                category=Category.objects.first(), vendor=Vendor.objects.first(),
            )
        html = self._html()
        self.assertIn('id="pagination-area"', html)

        grid = block_owned_by(html, "filtered-product-grid")

        self.assertNotIn('id="pagination-area"', grid)
        self.assertNotIn('class="page-link"', grid)

    def test_the_page_has_balanced_div_tags(self):
        """Chốt luôn nguyên nhân, không chỉ triệu chứng.

        Trước bước 2.8 file này thừa đúng một thẻ `<div>` không đóng. Trình duyệt tự vá
        nên nhìn bằng mắt không thấy gì sai — chỉ có JS ghi đè mới lộ ra.
        """
        html = self._html()

        self.assertEqual(
            len(DIV_OPEN.findall(html)), len(DIV_CLOSE.findall(html)),
            "Số thẻ <div> mở và đóng không khớp trên trang danh sách sản phẩm",
        )
