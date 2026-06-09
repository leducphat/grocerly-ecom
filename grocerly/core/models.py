from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from userauths.models import User
from taggit.managers import TaggableManager
from django.utils import timezone


STATUS_CHOICES = (
    ('processing', 'Processing'),
    ('shipped', 'Shipped'),
    ('delivered', 'Delivered'),
)

PAYMENT_METHOD_CHOICES = (
    ('online', 'Online'),
    ('cod', 'Cash on Delivery'),
)

STATUS = (
    ('draft', 'Draft'),
    ('disabled', 'Disabled'),
    ('in_review', 'In Review'),
    ('rejected', 'Rejected'),
    ('published', 'Published'),
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
     - MyModel.all_objects.dead()        → only deleted items
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
        # Cascade soft-delete to all products belonging to this vendor
        Product.all_objects.filter(vendor=self, is_deleted=False).update(
            is_deleted=True, deleted_at=timezone.now()
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

    product_status = models.CharField(max_length=10, choices=STATUS, default='in_review')

    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False) # physical or digital product (digital products do not require shipping address)
    
    sku = ShortUUIDField(unique=True, length=10, max_length=20, prefix="sku", alphabet="1234567890")

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)

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

class CartOrderItem(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)
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

    def __str__(self):
        return f"{self.code}"