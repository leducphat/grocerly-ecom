"""Thứ tự truy vấn của các trang danh sách — PLAN bước 2.8, tiền đề của phân trang.

⚠️ **Nhóm test này bắt loại lỗi KHÔNG tái hiện được ở máy local.**

`settings_local` và `settings_test` đều ép SQLite, mà SQLite gần như luôn trả bản ghi
theo rowid tăng dần khi truy vấn không có `ORDER BY` — nhìn y hệt như đã sắp đúng.
Production là PostgreSQL trên Neon, ở đó thứ tự khi thiếu `ORDER BY` là **không xác
định**: thêm `LIMIT`/`OFFSET` của phân trang lên trên nó thì cùng một bản ghi có thể hiện
ở cả trang 1 lẫn trang 2, hoặc không hiện ở trang nào.

Vì vậy các test dưới đây khẳng định **cấu trúc truy vấn** (`qs.ordered`,
`qs.query.order_by`) chứ không khẳng định "mở trang 2 thấy có dữ liệu" — kiểu sau vẫn
xanh trên SQLite kể cả khi thiếu `order_by`, tức là không bắt được gì.

Không dùng `Meta.ordering`: nó áp lên **mọi** truy vấn của model, kể cả `store_api` và
Django admin, và là hành vi ngầm — trong khi repo này vốn viết `.order_by()` tường minh
ở từng view.
"""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import CartOrder, Category, Product, ProductReview, Vendor, Wishlist
from userauths.models import User


class StorefrontOrderingTests(TestCase):
    """Mọi queryset sắp được phân trang phải có thứ tự xác định."""

    def setUp(self):
        self.category = Category.objects.create(title="Trái cây")
        self.vendor = Vendor.objects.create(name="Vinamilk")
        for i in range(3):
            Product.objects.create(
                title=f"Dưa hấu {i}", price=Decimal("50000.00"),
                product_status='published', category=self.category, vendor=self.vendor,
            )

    def _products_from(self, url_name, *args, **params):
        """Trả về **queryset gốc** phía sau trang, không phải đối tượng `Page`.

        Từ bước 2.8 các view này đặt một `Page` vào context. `Page` không có `.ordered`
        và cũng không phải chỗ cần kiểm — thứ phải có `ORDER BY` là queryset mà
        `Paginator` cắt `LIMIT/OFFSET` lên trên.
        """
        response = self.client.get(reverse(url_name, args=args), params)
        self.assertEqual(response.status_code, 200)
        page = response.context['products']
        return page.paginator.object_list

    def test_the_product_list_is_ordered(self):
        self.assertTrue(self._products_from("core:product-list").ordered)

    def test_the_category_page_is_ordered(self):
        products = self._products_from(
            "core:category-product-list", self.category.c_id
        )
        self.assertTrue(products.ordered)

    def test_the_vendor_page_is_ordered(self):
        products = self._products_from("core:vendor-detail", self.vendor.v_id)
        self.assertTrue(products.ordered)

    def test_the_search_page_is_ordered(self):
        self.assertTrue(self._products_from("core:search", q="Dưa").ordered)

    def test_the_search_page_breaks_ties_by_id(self):
        """`Product.date` là `auto_now_add` và **không unique**.

        Sắp mỗi theo `-date` thì hai sản phẩm tạo trong cùng một tick vẫn nhập nhằng —
        đúng loại nhập nhằng mà `LIMIT/OFFSET` biến thành bản ghi trùng giữa các trang.
        Test này chốt tiêu chí phá hòa, thứ mà `.ordered` không nhìn thấy.
        """
        order_by = self._products_from("core:search", q="Dưa").query.order_by

        self.assertEqual(tuple(order_by), ('-date', '-id'))

    def test_the_category_list_is_ordered(self):
        response = self.client.get(reverse("core:category-list"))

        self.assertTrue(response.context['categories'].ordered)

    def test_the_vendor_list_is_ordered(self):
        response = self.client.get(reverse("core:vendor-list"))

        self.assertTrue(response.context['vendors'].ordered)


class WishlistOrderingTests(TestCase):
    """Cặp "view thường + endpoint AJAX" phải sắp giống nhau.

    `wishlist_view` và `remove_wishlist` dựng **cùng một** queryset ở hai chỗ khác nhau
    trong `core/views.py`. Sửa một nửa là danh sách nhảy thứ tự ngay sau khi khách xóa
    một mục — đúng kiểu lỗi PLAN bước 2.3 đã gặp với `cart.html` và bản async của nó.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau123",
        )
        self.client.force_login(self.user)
        category = Category.objects.create(title="Trái cây")
        vendor = Vendor.objects.create(name="Vinamilk")
        self.product = Product.objects.create(
            title="Dưa hấu", price=Decimal("50000.00"), product_status='published',
            category=category, vendor=vendor,
        )
        Wishlist.objects.create(user=self.user, product=self.product)

    def test_the_wishlist_page_is_ordered(self):
        response = self.client.get(reverse("core:wishlist"))

        self.assertTrue(response.context['w'].ordered)

    def test_the_wishlist_ajax_list_is_ordered_too(self):
        other = Product.objects.create(
            title="Xoài cát", price=Decimal("70000.00"), product_status='published',
        )
        Wishlist.objects.create(user=self.user, product=other)

        response = self.client.get(
            reverse("core:remove-from-wishlist"), {'id': Wishlist.objects.first().id}
        )

        self.assertEqual(response.status_code, 200)
        # Không đọc được queryset qua JsonResponse, nên chốt gián tiếp: bản async render
        # ra đúng số mục còn lại và không nổ.
        self.assertEqual(response.json()['total_wishlist_items'], 1)


class StaffListOrderingTests(TestCase):
    """Phía nhân viên — không phân trang (trừ đơn hàng) nhưng thứ tự vẫn phải xác định."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="nhanvien", email="nv@grocerly.vn", password="matkhau123",
            is_staff=True,
        )
        self.client.force_login(self.staff)
        for _ in range(3):
            CartOrder.objects.create(user=self.staff, price=Decimal("50000.00"))

    def test_the_staff_order_list_is_ordered(self):
        response = self.client.get(reverse("useradmin:orders"))

        self.assertTrue(response.context['orders'].ordered)

    def test_the_staff_review_list_is_ordered(self):
        response = self.client.get(reverse("useradmin:reviews"))

        self.assertTrue(response.context['reviews'].ordered)

    def test_the_shop_page_product_list_is_ordered(self):
        response = self.client.get(reverse("useradmin:shop_page"))

        self.assertTrue(response.context['products'].ordered)

    def test_the_dashboard_latest_orders_really_are_the_latest(self):
        """Biến tên là `latest_orders` nhưng trước đây không sắp xếp gì cả."""
        newest = CartOrder.objects.create(user=self.staff, price=Decimal("99000.00"))

        response = self.client.get(reverse("useradmin:dashboard"))

        self.assertEqual(list(response.context['latest_orders'])[0], newest)
