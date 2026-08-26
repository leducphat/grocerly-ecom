from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from taggit.managers import TaggableManager
from django.utils import timezone


# Trạng thái GIAO HÀNG của đơn (khác hẳn `STATUS` của Product bên dưới — Bẫy #1).
#
# `cancelled` thêm ở PLAN bước 2.10 (UC 3.2.25, SPEC-GAPS A7). Nó là trạng thái **cuối**,
# giống `delivered`: đơn đã hủy không quay lại được.
#
# Chỉ hủy được đơn còn ở `processing`, không hủy đơn đã `shipped`. Đây không phải quy tắc
# tùy tiện mà là ràng buộc của tồn kho: kho chỉ bị trừ khi đơn chuyển sang `shipped`
# (`change_order_status`), nên hủy trước mốc đó **không cần hoàn kho** — không có nhánh
# hoàn kho nào để viết sai.
STATUS_CHOICES = (
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
    ('cancelled', 'Cancelled'),
)

PAYMENT_METHOD_CHOICES = (
    ('online', 'Online'),
    ('cod', 'Cash on Delivery'),
)

# Không có bước duyệt: nhân viên tự quyết khi nào sản phẩm sẵn sàng (ADR-0002).
# 'in_review' và 'rejected' đã bị bỏ ở migration 0005.
STATUS = (
    ('draft', 'Draft'),
    ('published', 'Published'),
    ('disabled', 'Disabled'),
)

RATING = (
    (1, "★☆☆☆☆"),
    (2, "★★☆☆☆"),
    (3, "★★★☆☆"),
    (4, "★★★★☆"),
    (5, "★★★★★"),
)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)


################################################# Soft Delete Infrastructure ##########################################
################################################# Soft Delete Infrastructure ##########################################

class SoftDeleteQuerySet(models.QuerySet):
    """Custom QuerySet that filters out soft-deleted objects by default."""

    def delete(self):
        """Soft-delete all objects in this queryset."""
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently delete all objects in this queryset."""
        return super().delete()

    def alive(self):
        """Return only non-deleted objects."""
        return self.filter(is_deleted=False)

    def dead(self):
        """Return only soft-deleted objects."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    """Manager that includes ALL objects (even soft-deleted ones)."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft-delete functionality.

    Usage:
     - MyModel.objects.all()             → only non-deleted items
     - MyModel.all_objects.all()         → everything (including deleted)
     - MyModel.all_objects.all().dead()  → only deleted items

    Lưu ý `.all()` ở dòng cuối: `dead()`/`alive()` là phương thức của *QuerySet*, không
    được proxy lên manager (muốn vậy phải dựng manager bằng `Manager.from_queryset`).
    Gọi thẳng `all_objects.dead()` sẽ ném `AttributeError`.
     - instance.soft_delete()            → mark as deleted
     - instance.restore()               → undo soft delete
     - instance.hard_delete()            → permanently remove from DB
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        """Mark this object as deleted."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Undo a soft delete."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self):
        """Permanently delete this object from the database."""
        super().delete()


################################################# Core Models ##########################################
################################################# Core Models ##########################################


class Category(SoftDeleteModel):
    c_id = ShortUUIDField(unique=True, length=10, max_length=20, prefix="cat", alphabet="abcdefgh12345")
    title = models.CharField(max_length=100, default="Category Title")
    image = models.ImageField(upload_to="category", default="category.jpg")

    class Meta:
        verbose_name_plural = "Categories"

    def category_image(self):
        return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
    
    def product_count(self):
        return Product.objects.filter(category=self).count()

    def __str__(self):
        return self.title
    

class Tag(models.Model):
    pass

class Vendor(SoftDeleteModel):
    v_id = ShortUUIDField(unique=True, length=10, max_length=20, prefix="ven", alphabet="abcdefgh12345")

    name = models.CharField(max_length=100, default="Vendor Name")
    image = models.ImageField(upload_to=user_directory_path, default="vendors.jpg")
    cover_image = models.ImageField(upload_to=user_directory_path, default="vendors.jpg")
    description = models.TextField(null=True, blank=True, default="No vendor's description available")

    address = models.CharField(max_length=100, default="123 Main Street")
    contact = models.CharField(max_length=100, default="+123 (456) 789")
    chat_resp_time = models.CharField(max_length=100, default="100")
    shipping_on_time = models.CharField(max_length=100, default="100")
    authentic_rating = models.CharField(max_length=100, default="100")
    days_return = models.CharField(max_length=100, default="100")
    warranty_period = models.CharField(max_length=100, default="100")


    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Vendors"

    def vendor_image(self):
        return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
    
    def __str__(self):
        return self.name

    def soft_delete(self):
        """Soft-delete this vendor and all their products."""
        super().soft_delete()
        # Cascade soft-delete to all products belonging to this vendor.
        #
        # Phải dùng CHÍNH `self.deleted_at`, không gọi `timezone.now()` lần nữa:
        # `restore()` bên dưới tìm lại nhóm sản phẩm bằng `filter(deleted_at=...)`, mà
        # hai lần gọi `now()` luôn lệch nhau vài trăm micro giây. Trước khi sửa, không
        # dòng nào khớp nên sản phẩm **không bao giờ được khôi phục** — vendor sống lại
        # một mình với gian hàng trống.
        Product.all_objects.filter(vendor=self, is_deleted=False).update(
            is_deleted=True, deleted_at=self.deleted_at
        )

    def restore(self):
        """Restore this vendor and all their products that were deleted at the same time."""
        deleted_at = self.deleted_at
        super().restore()
        # Restore products that were soft-deleted at the same time as this vendor
        if deleted_at:
            Product.all_objects.filter(vendor=self, deleted_at=deleted_at).update(
                is_deleted=False, deleted_at=None
            )


class ProductQuerySet(SoftDeleteQuerySet):
    def published(self):
        """Sản phẩm đang được bán — điều kiện hiển thị duy nhất của storefront và API."""
        return self.filter(product_status='published')


class ProductManager(SoftDeleteManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db).alive()

    def published(self):
        return self.get_queryset().published()


class ProductAllObjectsManager(AllObjectsManager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)


class Product(SoftDeleteModel):
    p_id = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefgh12345")

    title = models.CharField(max_length=100, default="Product Title")
    image = models.ImageField(upload_to="products", default="products.jpg")
    description = models.TextField(null=True, blank=True, default="No product's description available")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, related_name='products')


    price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    old_price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)

    specification = models.TextField(null=True, blank=True, default="No product's specification available")
    weight_volume = models.CharField(max_length=100, null=True, blank=True, default="1 kg")
    ingredients = models.TextField(null=True, blank=True, default="Đang cập nhật")
    storage_instructions = models.CharField(max_length=255, null=True, blank=True, default="Bảo quản nơi khô ráo, thoáng mát")
    stock_count = models.IntegerField(default=0, null=True, blank=True)
    expiry_period = models.CharField(max_length=100, null=True, blank=True, default="N/A")
    tags = TaggableManager(blank=True)

    product_status = models.CharField(max_length=10, choices=STATUS, default='draft')

    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False) # physical or digital product (digital products do not require shipping address)
    
    sku = ShortUUIDField(unique=True, length=10, max_length=20, prefix="sku", alphabet="1234567890")

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)

    # Ghi đè manager của SoftDeleteModel để có thêm .published().
    # Thứ tự khai báo giữ nguyên nên `objects` vẫn là _default_manager.
    objects = ProductManager()
    all_objects = ProductAllObjectsManager()

    class Meta:
        verbose_name_plural = "Products"

    def product_image(self):
        return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
    
    def __str__(self):
        return self.title
    
    def get_percentage(self):
        if self.old_price > 0:
            discount = ((self.old_price - self.price) / self.old_price) * 100
            return int(discount)
        return 0
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='p_image')
    image = models.ImageField(upload_to="product-images", default="product.jpg")
    date = models.DateTimeField(auto_now_add=True)




################################################# Cart, Order, OrderItem ##########################################
################################################# Cart, Order, OrderItem ##########################################
################################################# Cart, Order, OrderItem ##########################################
################################################# Cart, Order, OrderItem ##########################################


class CartOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)

    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    saved = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    coupons = models.ManyToManyField('Coupon', blank=True)

    shipping_method = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online')
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    tracking_website_address = models.CharField(max_length=100, null=True, blank=True)

    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    product_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='processing')
    sku = ShortUUIDField(null=True, blank=True, length=5, prefix="SKU", max_length=20, alphabet="1234567890")
    oid = ShortUUIDField(null=True, blank=True, length=8, max_length=20, alphabet="1234567890")

    date = models.DateTimeField(default=timezone.now, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Cart Orders"

    def confirm_paid(self):
        """Đánh dấu đơn đã thu tiền. Điểm duy nhất **trong code ứng dụng** được phép ghi
        `paid_status=True`.

        ⚠️ Django admin **không** đi qua đây: `CartOrderAdmin` không khai `fields` nên
        form sinh ra có cả ô `paid_status` lẫn ô sửa M2M `coupons`. Quản trị viên tick
        thẳng vào đó là bộ đếm `used_count` **không tăng**, và hạn mức của mã giảm giá
        mất hiệu lực im lặng. Xem nợ kỹ thuật #10 ở docs/ARCHITECTURE.md.

        Trả `True` nếu lần này thực sự chuyển trạng thái, `False` nếu đơn vốn đã trả rồi.

        Gom về một chỗ vì đây cũng là nơi tăng bộ đếm lượt dùng của mã giảm giá
        (PLAN bước 2.9). Ba đường xác nhận thanh toán — `vnpay_return`, `vnpay_ipn`,
        và nhân viên đánh dấu đơn COD đã giao — nếu mỗi đường tự tăng bộ đếm thì:

        - `vnpay_return` (trình duyệt khách quay về) và `vnpay_ipn` (VNPay gọi server)
          có thể **cùng chạy cho một đơn**, thành +2 lượt cho một lần mua. Trước bước
          này `vnpay_ipn` có chốt `if order.paid_status` còn `vnpay_return` thì không.
        - Thêm một đường thanh toán mới là quên tăng bộ đếm ở đó.

        Tăng bộ đếm ở đây chứ **không** ở lúc áp mã: khách áp mã rồi bỏ đi thì đơn treo
        mãi ở `paid_status=False`, và `save_checkout_info` gọi `coupons.clear()` mỗi lần
        khách sửa giỏ nên áp lại là cộng thêm một lượt nữa cho cùng một đơn.

        Đánh đổi đã biết: kiểm "còn lượt không" ở lúc áp mã, tăng ở lúc trả tiền — hai
        thời điểm cách nhau tùy ý nên vẫn có thể vượt hạn mức nếu nhiều khách áp cùng
        lúc. Chấp nhận: không có luồng hoàn tiền (ADR-0007) nên bộ đếm chỉ đi một chiều.

        ⚠️ `select_for_update()` **không có tác dụng trên SQLite** (cả `settings_test` lẫn
        `settings_local` đều ép SQLite). Test chứng minh được tính idempotent, không
        chứng minh được chống tranh chấp.
        """
        from django.db import transaction
        from django.db.models import F

        with transaction.atomic():
            locked = CartOrder.objects.select_for_update().get(pk=self.pk)
            if locked.paid_status:
                return False

            # `all_objects`: mã bị xóa mềm sau khi khách đã áp thì bộ đếm vẫn phải đúng.
            Coupon.all_objects.filter(cartorder=locked).update(
                used_count=F('used_count') + 1
            )
            locked.paid_status = True
            locked.save(update_fields=['paid_status'])

        self.paid_status = True
        return True

class CartOrderItem(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)

    # Khóa ngoại đặt SONG SONG với bản sao tĩnh bên dưới, không thay nó (ADR-0006).
    #
    # `item`/`image`/`price` vẫn là ảnh chụp tại thời điểm đặt hàng: hóa đơn của khách
    # không được đổi khi nhân viên sửa giá hay đổi tên sản phẩm. Cái khóa ngoại thêm vào
    # là **đường tra ngược** — trả lời được "người này đã mua sản phẩm kia chưa" mà không
    # phải đoán theo tên (nợ kỹ thuật #6).
    #
    # SET_NULL chứ không CASCADE: xóa cứng một sản phẩm **không được** làm bốc hơi dòng
    # hóa đơn của khách. Mất khóa ngoại thì bản sao tĩnh vẫn còn nguyên.
    #
    # NULL còn có nghĩa thứ hai: dòng cũ có từ trước migration 0007 mà backfill không
    # dò ra sản phẩm gốc. Đừng đọc NULL thành "sản phẩm này chưa từng bán".
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items',
    )

    invoice_no = models.CharField(max_length=200)
    product_status = models.CharField(max_length=200)
    item = models.CharField(max_length=200)
    image = models.CharField(max_length=200)
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)

    class Meta:
        verbose_name_plural = "Cart Order Items"

    def order_image(self):
        return mark_safe(f'<img src="/media/{self.image}" width="50" height="50" />')
    


################################################# ProductReview, Wishlist, Address ##########################################
################################################# ProductReview, Wishlist, Address ##########################################
################################################# ProductReview, Wishlist, Address ##########################################
################################################# ProductReview, Wishlist, Address ##########################################


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        if self.product:
            return self.product.title
        return f"Review #{self.pk}"
    
    def get_rating(self):
        return self.rating


class Wishlist(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Wishlists"

    def __str__(self):
        if self.product:
            return self.product.title
        return f"Wishlist #{self.pk}"


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    mobile = models.CharField(max_length=300, null=True)
    address = models.CharField(max_length=100, null=True)
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"


class Coupon(SoftDeleteModel):
    code = models.CharField(max_length=1000)
    discount = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    # PLAN bước 2.9 — UC 3.2.21, SPEC-GAPS A6. Cả ba đều nullable hoặc có default nên
    # migration KHÔNG cần backfill: mã đang có trên production giữ nguyên nghĩa "không
    # hết hạn, không giới hạn lượt".
    #
    # `default=timezone.now` chứ không `auto_now_add`: `auto_now_add` đánh field thành
    # non-editable, tức là nó **biến mất khỏi form admin** và quản trị viên không đặt
    # được hạn dùng. Sáu `DateTimeField` khác trong file này dùng `auto_now_add`, chép
    # theo thói quen là rơi đúng bẫy đó.
    valid_to = models.DateTimeField(
        null=True, blank=True,
        help_text="Bỏ trống nghĩa là mã không bao giờ hết hạn.",
    )
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Số lượt tối đa. Bỏ trống nghĩa là không giới hạn.",
    )
    used_count = models.PositiveIntegerField(
        default=0,
        help_text="Số lượt đã dùng. Chỉ tăng khi đơn hàng được xác nhận đã thanh toán.",
    )

    # Khóa lỗi trả về từ `usable_error()`. Để view tự dịch sang thông điệp — model không
    # nên biết gì về i18n của tầng hiển thị.
    EXPIRED = 'expired'
    EXHAUSTED = 'exhausted'

    def usable_error(self):
        """`None` nếu mã còn dùng được, ngược lại trả khóa lỗi.

        Đặt trên model chứ không viết thẳng `if` vào `checkout()`: như vậy unit test
        được mà không phải dựng HTTP, và `checkout()` giữ được độ mỏng.

        ⚠️ Hàm này **không** kiểm `active` và **không** kiểm xóa mềm. Hai điều kiện đó
        nằm ở truy vấn tra mã (`Coupon.objects.filter(code=..., active=True)`) — `objects`
        là `SoftDeleteManager`. Đừng chuyển chúng vào đây rồi đổi truy vấn sang
        `all_objects`: `core/test_softdelete.py` chốt đúng hành vi của truy vấn đó.
        """
        if self.valid_to is not None and self.valid_to < timezone.now():
            return self.EXPIRED
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return self.EXHAUSTED
        return None

    def __str__(self):
        return f"{self.code}"