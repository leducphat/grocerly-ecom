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

# Create your models here.
class Category(models.Model):
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

class Vendor(models.Model):
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

    def vendor_image(self):
        return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
    
    def __str__(self):
        return self.name
        

class Product(models.Model):
    p_id = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefgh12345")

    title = models.CharField(max_length=100, default="Product Title")
    image = models.ImageField(upload_to="products", default="products.jpg")
    description = models.TextField(null=True, blank=True, default="No product's description available")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, related_name='products')


    price = models.DecimalField(max_digits=999999999999, decimal_places=3, default=0.000)
    old_price = models.DecimalField(max_digits=999999999999, decimal_places=3, default=1.000)

    specification = models.TextField(null=True, blank=True, default="No product's specification available")
    type = models.CharField(max_length=100, null=True, blank=True, default="General")
    stock_count = models.IntegerField(default=0, null=True, blank=True)
    expiry_period = models.CharField(max_length=100, null=True, blank=True, default="N/A")
    mfd = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    tags = TaggableManager(blank=True)

    product_status = models.CharField(max_length=10, choices=STATUS, default='in_review')

    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False) # physical or digital product (digital products do not require shipping address)
    
    sku = ShortUUIDField(unique=True, length=10, max_length=20, prefix="sku", alphabet="1234567890")

    date = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True)


    # quantity = models.IntegerField(default=1)
    # category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)

    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    coupons = models.ManyToManyField('Coupon', blank=True)

    shipping_method = models.CharField(max_length=100, null=True, blank=True)
    tracking_id = models.CharField(max_length=100, null=True, blank=True)
    tracking_website_address = models.CharField(max_length=100, null=True, blank=True)

    paid_status = models.BooleanField(default=False)
    order_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    product_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='processing')
    sku = ShortUUIDField(null=True, blank=True, length=5, prefix="SKU", max_length=20, alphabet="1234567890")
    oid = ShortUUIDField(null=True, blank=True, length=8, max_length=20, alphabet="1234567890")
    stripe_payment_intent = models.CharField(max_length=1000, null=True, blank=True)
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
    price = models.DecimalField(max_digits=999999999999, decimal_places=3, default=0.000)
    total = models.DecimalField(max_digits=999999999999, decimal_places=3, default=0.000)

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
        return self.product.title
    
    def get_rating(self):
        return self.rating


class Wishlist(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return self.product.title


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    mobile = models.CharField(max_length=300, null=True)
    address = models.CharField(max_length=100, null=True)
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"


class Coupon(models.Model):
    code = models.CharField(max_length=1000)
    discount = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code}"