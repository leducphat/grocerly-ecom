from core.models import Category, Tag, Vendor, Product, ProductReview, ProductImage, CartOrder, CartOrderItem, Wishlist, Address

def default(request):
    categories = Category.objects.all()
    return {
        'categories': categories
    }