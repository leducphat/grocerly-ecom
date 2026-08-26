from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from urllib.parse import urlencode

from core.models import Category, Tag, Vendor, Product, ProductReview, ProductImage, CartOrder, CartOrderItem, Wishlist, Address, Coupon


# ======================== Soft Delete Admin Mixin ========================

class SoftDeleteAdminMixin:
    """
    Mixin for admin classes of SoftDeleteModel subclasses.
    - Shows all objects (including deleted) via all_objects manager.
    - Adds 'is_deleted' to list_display and list_filter.
    - Provides bulk actions to soft-delete and restore.
    """

    def get_queryset(self, request):
        """Show ALL objects in admin, including soft-deleted ones."""
        return self.model.all_objects.get_queryset()

    def soft_delete_selected(self, request, queryset):
        count = queryset.filter(is_deleted=False).update(
            is_deleted=True,
            deleted_at=__import__('django.utils.timezone', fromlist=['now']).now()
        )
        self.message_user(request, f"{count} item(s) soft-deleted.")

    soft_delete_selected.short_description = "Soft delete selected items"

    def restore_selected(self, request, queryset):
        count = queryset.filter(is_deleted=True).update(
            is_deleted=False,
            deleted_at=None
        )
        self.message_user(request, f"{count} item(s) restored.")

    restore_selected.short_description = "Restore selected items"

    actions = ['soft_delete_selected', 'restore_selected']


# ======================== Core Model Admins ========================

class ProductImagesAdmin(admin.TabularInline):
    model = ProductImage

class ProductAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_display = ['user', 'title', 'product_image', 'category', 'vendor', 'price', 'old_price', 'get_percentage', 'featured', 'product_status', 'is_deleted', 'p_id']
    list_filter = ['is_deleted', 'product_status', 'featured', 'category', 'vendor']

class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'category_image', 'is_deleted']
    list_filter = ['is_deleted']

class VendorAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'vendor_image', 'is_deleted']
    list_filter = ['is_deleted']


class CartOrderItemInline(admin.TabularInline):
    model = CartOrderItem
    extra = 0
    fields = ['invoice_no', 'item', 'quantity', 'price', 'total', 'product_status']
    readonly_fields = ['invoice_no', 'item', 'quantity', 'price', 'total', 'product_status']

class CartOrderAdmin(admin.ModelAdmin):
    list_display = ['customer_type', 'user', 'email', 'payment_method', 'price', 'paid_status', 'order_date', 'product_status', 'oid_link']
    list_filter = ['paid_status', 'payment_method', 'product_status', 'order_date']
    search_fields = ['oid', 'email', 'full_name', 'phone', 'user__email', 'user__username']
    inlines = [CartOrderItemInline]

    def customer_type(self, obj):
        return "Registered" if obj.user else "Guest"

    customer_type.short_description = "Customer Type"

    def oid_link(self, obj):
        changelist_url = reverse('admin:core_cartorderitem_changelist')
        query_string = urlencode({'q': obj.oid})
        return format_html('<a href="{}?{}">{}</a>', changelist_url, query_string, obj.oid)

    oid_link.short_description = "OID"
    oid_link.admin_order_field = 'oid'

class CartOrderItemsAdmin(admin.ModelAdmin):
    list_display = ['order_oid', 'order', 'invoice_no', 'item', 'order_image', 'quantity', 'price', 'total']
    list_filter = ['product_status']
    search_fields = ['invoice_no', 'item', 'order__oid', 'order__email', 'order__user__email']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'order__user')

    def order_oid(self, obj):
        return obj.order.oid

    order_oid.short_description = 'Order OID'
    order_oid.admin_order_field = 'order__oid'

class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'review', 'rating']

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product']

class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'address', 'mobile', 'status']

class CouponAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['code', 'discount', 'active', 'valid_to', 'used_count', 'usage_limit', 'is_deleted']
    list_filter = ['is_deleted', 'active']
    # `used_count` do hệ thống tăng khi đơn được xác nhận đã thanh toán
    # (`CartOrder.confirm_paid`). Không khai `fields`/`fieldsets` nên Django tự sinh form
    # từ MỌI field editable — thiếu dòng này là quản trị viên gõ tay được vào bộ đếm.
    readonly_fields = ['used_count']


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItem, CartOrderItemsAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(Wishlist, WishlistAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Coupon, CouponAdmin)