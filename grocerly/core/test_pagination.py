"""Phân trang các trang danh sách sản phẩm — PLAN bước 2.8, SPEC-GAPS A3 (UC 3.2.3).

Năm trang được phân trang: danh sách sản phẩm, sản phẩm theo danh mục, theo thương hiệu,
tìm kiếm, theo tag. Danh sách danh mục và danh sách thương hiệu **cố ý không** phân trang
— Grocerly là một siêu thị (ADR-0003) nên hai danh sách đó nhỏ và ổn định.

Ba nhóm dễ sai mà file này nhắm vào:

1. **Tham số `page` hỏng.** Đây là chỗ người dùng và bot sửa URL nhiều nhất; `?page=abc`
   hay `?page=999` không được thành lỗi 500.
2. **Mất querystring.** Link sang trang 2 của trang tìm kiếm mà rơi mất `?q=` thì trang 2
   trả về toàn bộ sản phẩm — lỗi kinh điển của phân trang tự nối chuỗi.
3. **Bộ lọc AJAX.** `filter_product` trả về HTML rời, phải trả **tổng** số kết quả chứ
   không phải số thẻ của một trang, và phải trả kèm HTML thanh phân trang vì thanh đó
   nằm ngoài vùng mà JS ghi đè.
"""

import re

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import Category, Product, Vendor
from core.views import PRODUCTS_PER_PAGE


class PaginationTestCase(TestCase):

    def setUp(self):
        self.category = Category.objects.create(title="Trái cây")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        # 20 sản phẩm = 3 trang với cỡ trang 8. Đủ để trang 2 vừa không phải trang đầu
        # vừa không phải trang cuối.
        self.products = [
            Product.objects.create(
                title=f"Dưa hấu {i:02d}", price=Decimal("50000.00"),
                product_status='published', category=self.category, vendor=self.vendor,
            )
            for i in range(20)
        ]

    def page_ids(self, url, **params):
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        return {p.p_id for p in response.context['products']}


class ProductListPaginationTests(PaginationTestCase):

    def setUp(self):
        super().setUp()
        self.url = reverse("core:product-list")

    def test_the_first_page_holds_one_page_worth_of_products(self):
        self.assertEqual(len(self.page_ids(self.url)), PRODUCTS_PER_PAGE)

    def test_the_second_page_shows_different_products(self):
        """Trang 1 và trang 2 không được giao nhau, và hợp lại phải đủ 16.

        Đây là test bắt lỗi trùng/mất bản ghi giữa các trang — hệ quả của việc phân trang
        một queryset không có `ORDER BY` (xem `core/test_ordering.py`).
        """
        first = self.page_ids(self.url)
        second = self.page_ids(self.url, page=2)

        self.assertEqual(first & second, set())
        self.assertEqual(len(first | second), 2 * PRODUCTS_PER_PAGE)

    def test_the_last_page_holds_the_remainder(self):
        self.assertEqual(len(self.page_ids(self.url, page=3)), 20 - 2 * PRODUCTS_PER_PAGE)

    def test_every_product_appears_exactly_once_across_all_pages(self):
        seen = []
        for number in (1, 2, 3):
            response = self.client.get(self.url, {'page': number})
            seen += [p.p_id for p in response.context['products']]

        self.assertEqual(len(seen), 20)
        self.assertEqual(len(set(seen)), 20)

    def test_a_non_numeric_page_falls_back_to_the_first_page(self):
        response = self.client.get(self.url, {'page': 'abc'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['products'].number, 1)

    def test_a_page_beyond_the_last_one_lands_on_the_last_page(self):
        response = self.client.get(self.url, {'page': 999})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['products'].number, 3)

    def test_a_negative_page_does_not_crash(self):
        self.assertEqual(self.client.get(self.url, {'page': -1}).status_code, 200)

    def test_the_product_count_is_the_total_not_the_page_size(self):
        """Dòng "We found N items" phải nói tổng, không nói số thẻ đang hiện."""
        response = self.client.get(self.url)

        self.assertEqual(response.context['product_count'], 20)

    def test_the_price_slider_still_sees_every_price(self):
        """`aggregate()` phải chạy TRƯỚC khi cắt trang.

        Nếu paginate trước thì `aggregate` ném `AttributeError` (đối tượng `Page` không
        phải QuerySet) — hoặc tệ hơn, thanh trượt giá chỉ còn khoảng giá của một trang.
        """
        Product.objects.create(
            title="Sầu riêng", price=Decimal("900000.00"), product_status='published',
            category=self.category, vendor=self.vendor,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.context['max_price'], Decimal("900000.00"))

    def test_the_bar_is_hidden_when_everything_fits_on_one_page(self):
        Product.objects.all().delete()
        Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), product_status='published',
            category=self.category, vendor=self.vendor,
        )

        response = self.client.get(self.url)

        self.assertNotContains(response, 'class="page-link"')


class SearchPaginationTests(PaginationTestCase):

    def test_the_search_page_paginates(self):
        response = self.client.get(reverse("core:search"), {'q': "Dưa"})

        self.assertEqual(len(response.context['products']), PRODUCTS_PER_PAGE)

    def test_page_two_of_a_search_still_filters_by_the_query(self):
        Product.objects.create(
            title="Xoài cát", price=Decimal("70000.00"), product_status='published',
            category=self.category, vendor=self.vendor,
        )

        response = self.client.get(reverse("core:search"), {'q': "Dưa", 'page': 2})

        titles = [p.title for p in response.context['products']]
        self.assertTrue(titles)
        self.assertTrue(all("Dưa" in t for t in titles))

    def test_the_page_links_keep_the_search_query(self):
        """Link phân trang mất `?q=` là trang 2 trả về toàn bộ sản phẩm.

        Phải bóc `href` ra mà kiểm, không dùng `assertContains` với một mẩu chuỗi: trang
        tìm kiếm có sẵn nhiều chỗ khác chứa `q=`, nên kiểu kiểm đó vẫn xanh kể cả khi
        thanh phân trang tự nối `?page=N` và đánh rơi từ khóa (đã thử, nó không đỏ).
        """
        response = self.client.get(reverse("core:search"), {'q': "Dưa"})

        hrefs = re.findall(
            r'<a class="page-link"[^>]*href="([^"]*)"', response.content.decode()
        )
        self.assertTrue(hrefs, "Không tìm thấy link phân trang nào")
        for href in hrefs:
            with self.subTest(href=href):
                self.assertIn("q=", href)
                self.assertIn("page=", href)

    def test_a_search_with_no_query_at_all_does_not_crash(self):
        """`request.GET.get("q")` không có default thì `icontains=None` ném lỗi."""
        self.assertEqual(self.client.get(reverse("core:search")).status_code, 200)


class CategoryVendorTagPaginationTests(PaginationTestCase):

    def test_the_category_page_paginates(self):
        url = reverse("core:category-product-list", args=[self.category.c_id])

        self.assertEqual(len(self.page_ids(url)), PRODUCTS_PER_PAGE)

    def test_the_vendor_page_paginates(self):
        url = reverse("core:vendor-detail", args=[self.vendor.v_id])

        self.assertEqual(len(self.page_ids(url)), PRODUCTS_PER_PAGE)

    def test_the_tag_page_does_not_double_count_a_product_with_several_tags(self):
        """Lọc qua quan hệ nhiều-nhiều mà thiếu `.distinct()` là đếm thừa.

        Sản phẩm gắn hai tag sẽ ra hai dòng, `Paginator.count` báo 2 trong khi chỉ có
        một thẻ hiện ra — số trang tính sai theo.
        """
        product = self.products[0]
        product.tags.add("khuyen-mai", "moi-ve")

        response = self.client.get(reverse("core:tags", args=["khuyen-mai"]))

        self.assertEqual(response.context['products'].paginator.count, 1)


class AjaxFilterPaginationTests(PaginationTestCase):

    def _filter(self, **params):
        response = self.client.get(reverse("core:filter-product"), params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_the_filter_reports_the_total_not_the_page_size(self):
        """`count` được ghi thẳng vào "We found N items" ở đầu trang."""
        self.assertEqual(self._filter()['count'], 20)

    def test_the_filter_returns_only_one_page_of_cards(self):
        payload = self._filter()

        self.assertEqual(payload['data'].count('product-cart-wrap'), PRODUCTS_PER_PAGE)

    def test_the_filter_returns_a_pagination_block(self):
        """Thanh phân trang nằm ngoài vùng JS ghi đè nên phải trả về riêng."""
        self.assertIn('class="page-link"', self._filter()['pagination'])

    def test_the_filter_honours_the_page_parameter(self):
        first = self._filter(page=1)['data']
        second = self._filter(page=2)['data']

        self.assertNotEqual(first, second)

    def test_a_broken_page_parameter_does_not_break_the_filter(self):
        self.assertEqual(self._filter(page='abc')['count'], 20)

    def test_filtering_narrows_the_total(self):
        other = Vendor.objects.create(name="TH True Milk")
        Product.objects.create(
            title="Sữa tươi", price=Decimal("30000.00"), product_status='published',
            category=self.category, vendor=other,
        )

        self.assertEqual(self._filter(vendor=other.id)['count'], 1)


class NoDeadPaginationLinksTests(PaginationTestCase):
    """Không trang nào được ship thanh phân trang giả của theme.

    Ba template từng render nguyên thanh phân trang tĩnh với `href="#"` — trông như có
    6 trang trong khi chỉ có một, và bấm vào thì không đi đâu cả.
    """

    def test_no_list_page_ships_a_dead_pagination_link(self):
        urls = [
            reverse("core:product-list"),
            reverse("core:category-product-list", args=[self.category.c_id]),
            reverse("core:vendor-detail", args=[self.vendor.v_id]),
            reverse("core:vendor-list"),
            reverse("core:category-list"),
            reverse("core:search") + "?q=Dưa",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, '<a class="page-link" href="#"')
