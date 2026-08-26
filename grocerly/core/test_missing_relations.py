"""Sản phẩm thiếu danh mục hoặc nhà cung cấp không được làm sập storefront.

`Product.category` và `Product.vendor` đều `null=True`, và `AddProductForm` để cả hai
`required=False` — nhân viên bấm Lưu mà chưa chọn danh mục là tạo được sản phẩm không có
`category`. `add_product` có giá trị dự phòng cho `vendor` (`Vendor.objects.first()`)
nhưng **không có** cho `category`.

Template lại gọi thẳng `{% url 'core:category-product-list' p.category.c_id %}`. Khi
`category` là None, Django template cho ra **chuỗi rỗng** thay vì ném lỗi, rồi `{% url %}`
nhận chuỗi rỗng và ném `NoReverseMatch` → **trang chủ trả 500 cho mọi khách**.

Phát hiện 2026-08-26 khi viết test cho checkout (bước 2.6f): test đỏ ở chỗ không ai ngờ,
vì `assertRedirects` đi theo redirect và render trang chủ.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import Category, Product, Vendor
from useradmin.forms import AddProductForm


class MissingRelationsTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(title="Trái cây")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        self.common = dict(
            price=Decimal("50000.00"), stock_count=10, product_status='published',
        )
        # Một sản phẩm đầy đủ để trang không rỗng — nếu rỗng thì vòng lặp template không
        # chạy và test sẽ xanh giả.
        Product.objects.create(
            title="Đầy đủ", category=self.category, vendor=self.vendor, **self.common
        )

    PAGES = ('core:index', 'core:product-list', 'core:search')

    def _visit_all(self):
        for name in self.PAGES:
            params = {'q': "Thiếu"} if name == 'core:search' else {}
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name), params).status_code, 200)

    def test_a_product_without_a_category_does_not_break_the_pages(self):
        Product.objects.create(
            title="Thiếu danh mục", category=None, vendor=self.vendor, **self.common
        )

        self._visit_all()

    def test_a_product_without_a_vendor_does_not_break_the_pages(self):
        Product.objects.create(
            title="Thiếu nhà cung cấp", category=self.category, vendor=None, **self.common
        )

        self._visit_all()

    def test_a_product_missing_both_does_not_break_the_pages(self):
        Product.objects.create(
            title="Thiếu cả hai", category=None, vendor=None, **self.common
        )

        self._visit_all()

    def test_the_ajax_product_filter_survives_too(self):
        """`core/async/product-list.html` có cùng hai chỗ gọi và cùng lỗi."""
        Product.objects.create(
            title="Thiếu cả hai", category=None, vendor=None, **self.common
        )

        response = self.client.get(reverse("core:filter-product"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Thiếu cả hai", response.json()['data'])

    def test_the_tag_page_survives_too(self):
        product = Product.objects.create(
            title="Thiếu cả hai", category=None, vendor=None, **self.common
        )
        product.tags.add("khuyến mãi")
        # Lấy slug do django-taggit sinh, không tự đoán cách nó slugify tiếng Việt.
        slug = product.tags.first().slug

        response = self.client.get(reverse("core:tags", args=[slug]))

        self.assertEqual(response.status_code, 200)

    def test_the_category_page_survives_a_product_without_a_vendor(self):
        Product.objects.create(
            title="Thiếu nhà cung cấp", category=self.category, vendor=None, **self.common
        )

        response = self.client.get(
            reverse("core:category-product-list", args=[self.category.c_id])
        )

        self.assertEqual(response.status_code, 200)

    def test_a_complete_product_still_shows_its_category_and_vendor(self):
        """Nhánh `{% if %}` không được nuốt mất thông tin của sản phẩm đầy đủ."""
        response = self.client.get(reverse("core:index"))

        self.assertContains(response, self.category.title)
        self.assertContains(response, self.vendor.name)
        self.assertContains(
            response, reverse("core:category-product-list", args=[self.category.c_id])
        )


class AddProductFormTests(TestCase):
    """Chốt lại vì sao dữ liệu thiếu quan hệ có thể tồn tại."""

    def test_the_staff_form_accepts_a_product_with_no_category(self):
        """Hành vi HIỆN TẠI, chưa phải kết luận là đúng.

        Nếu sau này quyết định bắt buộc chọn danh mục thì test này đỏ, buộc người sửa
        đọc ghi chú đầu file thay vì đổi âm thầm. Bản vá 2026-08-26 chỉ chặn việc **sập
        trang**, không đụng tới câu hỏi nghiệp vụ "danh mục có nên bắt buộc không".
        """
        form = AddProductForm(data={
            'title': "Không danh mục",
            'description': "mô tả",
            'price': "50000",
            'old_price': "60000",
            'specification': "spec",
            'stock_count': "10",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['category'])
