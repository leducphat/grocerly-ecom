"""Test hạ tầng xóa mềm — PLAN bước 2.6d.

`SoftDeleteModel` cấp cho `Category`, `Vendor`, `Product`, `Coupon`. Đây là chỗ có
**Bẫy #3** trong AGENTS.md: `delete()` chỉ được override ở tầng *QuerySet*, nên gọi
`instance.delete()` vẫn xóa vĩnh viễn. Bẫy đó tới nay chỉ tồn tại dưới dạng một dòng
trong tài liệu, không có gì chốt lại.

Phải chốt trước khi làm bước 2.1 (`delete_product` xóa mềm khi có đơn liên quan): sửa
một cơ chế xóa mà không có test mô tả cơ chế đó đang làm gì là sửa mù.

Lưu ý về tên gọi: đây **không phải unit test thuần** như `test_vnpay.py` — chúng cần
database nên dùng `TestCase`. Nhưng chúng test *model*, không đi qua HTTP, nên vẫn nằm
dưới tầng test hồi quy ở `tests.py`.
"""

from django.test import TestCase

from core.models import Category, Coupon, Product, Vendor


class SoftDeleteBasicsTests(TestCase):
    """Hành vi nền của `SoftDeleteModel`, kiểm trên `Category` cho gọn."""

    def setUp(self):
        self.category = Category.objects.create(title="Trái cây")

    def test_soft_delete_hides_from_objects_but_keeps_the_row(self):
        self.category.soft_delete()

        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
        self.assertTrue(Category.all_objects.filter(pk=self.category.pk).exists())

    def test_soft_delete_stamps_the_time(self):
        self.assertIsNone(self.category.deleted_at)

        self.category.soft_delete()

        self.assertTrue(self.category.is_deleted)
        self.assertIsNotNone(self.category.deleted_at)

    def test_restore_brings_it_back_and_clears_the_stamp(self):
        self.category.soft_delete()
        self.category.restore()

        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
        self.assertFalse(self.category.is_deleted)
        self.assertIsNone(self.category.deleted_at)

    def test_hard_delete_removes_the_row_for_good(self):
        self.category.hard_delete()

        self.assertFalse(Category.all_objects.filter(pk=self.category.pk).exists())

    def test_dead_and_alive_split_the_rows(self):
        gone = Category.objects.create(title="Đồ hộp")
        gone.soft_delete()

        # Cần `.all()` ở giữa: `dead()`/`alive()` là phương thức của QuerySet, không được
        # proxy lên manager. Docstring của `SoftDeleteModel` từng ghi thiếu chỗ này.
        self.assertEqual(list(Category.all_objects.all().dead()), [gone])
        self.assertEqual(list(Category.all_objects.all().alive()), [self.category])

    def test_dead_is_not_available_directly_on_the_manager(self):
        """Chốt cái bẫy vừa nêu: gọi tắt sẽ nổ, không phải trả về rỗng."""
        with self.assertRaises(AttributeError):
            Category.all_objects.dead()


class InstanceDeleteIsStillHardDeleteTests(TestCase):
    """**Bẫy #3** — `instance.delete()` xóa vĩnh viễn, KHÔNG xóa mềm.

    `SoftDeleteModel` không override `delete()`, chỉ `SoftDeleteQuerySet` mới có. Nghĩa
    là hai dòng trông giống hệt nhau lại cho kết quả trái ngược, và cái nguy hiểm hơn lại
    là cái ngắn hơn.

    Đây là hành vi **đang có**, chốt lại chứ chưa khẳng định là đúng. `delete_product`
    trong `useradmin` đang gọi đúng dạng nguy hiểm này — PLAN bước 2.1 sẽ xử lý.
    """

    def setUp(self):
        self.product = Product.objects.create(title="Dưa hấu", product_status='published')

    def test_instance_delete_wipes_the_row(self):
        pk = self.product.pk

        self.product.delete()

        self.assertFalse(Product.all_objects.filter(pk=pk).exists())

    def test_queryset_delete_only_soft_deletes(self):
        pk = self.product.pk

        Product.objects.filter(pk=pk).delete()

        self.assertFalse(Product.objects.filter(pk=pk).exists())
        self.assertTrue(Product.all_objects.filter(pk=pk).exists())

    def test_queryset_hard_delete_wipes_the_row(self):
        pk = self.product.pk

        Product.objects.filter(pk=pk).hard_delete()

        self.assertFalse(Product.all_objects.filter(pk=pk).exists())


class PublishedExcludesSoftDeletedTests(TestCase):
    """`published()` phải lọc CẢ hai điều kiện: đang bán **và** chưa xóa mềm.

    Hai cơ chế này độc lập nhau (`ProductManager.get_queryset()` gọi `.alive()`, rồi
    `.published()` lọc tiếp `product_status`). Không test thì không ai biết chúng có
    chồng lên nhau đúng cách không — mà đây là điều kiện hiển thị duy nhất của storefront
    lẫn `store_api` (SECURITY.md S-04).
    """

    def test_a_soft_deleted_published_product_is_not_published_anymore(self):
        product = Product.objects.create(title="Dưa hấu", product_status='published')
        self.assertIn(product, Product.objects.published())

        product.soft_delete()

        self.assertNotIn(product, Product.objects.published())


class VendorCascadeTests(TestCase):
    """`Vendor.soft_delete()` lan xuống sản phẩm; `restore()` khôi phục đúng nhóm đó.

    Đây là logic tinh vi nhất trong `core/models.py`: `restore()` không khôi phục mọi sản
    phẩm của vendor, mà chỉ những sản phẩm bị xóa **cùng thời điểm** với vendor — để sản
    phẩm đã bị xóa lẻ từ trước không vô tình sống lại.
    """

    def setUp(self):
        self.vendor = Vendor.objects.create(name="Vinamilk")
        self.product = Product.objects.create(
            title="Sữa tươi", vendor=self.vendor, product_status='published'
        )

    def test_soft_deleting_a_vendor_hides_its_products(self):
        self.vendor.soft_delete()

        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
        self.assertTrue(Product.all_objects.filter(pk=self.product.pk).exists())

    def test_restoring_a_vendor_brings_its_products_back(self):
        self.vendor.soft_delete()
        self.vendor.restore()

        self.assertTrue(
            Product.objects.filter(pk=self.product.pk).exists(),
            "Sản phẩm bị xóa cùng vendor phải sống lại khi vendor được khôi phục",
        )

    def test_a_product_deleted_earlier_stays_deleted_after_the_vendor_is_restored(self):
        earlier = Product.objects.create(
            title="Sữa chua", vendor=self.vendor, product_status='published'
        )
        earlier.soft_delete()

        self.vendor.soft_delete()
        self.vendor.restore()

        self.assertFalse(
            Product.objects.filter(pk=earlier.pk).exists(),
            "Sản phẩm đã bị xóa lẻ từ trước không được sống lại theo vendor",
        )


class CouponSoftDeleteTests(TestCase):
    """`Coupon` cũng kế thừa `SoftDeleteModel` — mã đã xóa không được áp dụng lại."""

    def test_soft_deleted_coupon_is_not_found_by_the_checkout_lookup(self):
        coupon = Coupon.objects.create(code="GIAM10", discount=10, active=True)
        coupon.soft_delete()

        # Đúng truy vấn mà `core.views.checkout` dùng để tra mã giảm giá.
        self.assertIsNone(Coupon.objects.filter(code="GIAM10", active=True).first())
