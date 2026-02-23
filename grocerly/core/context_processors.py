from core.models import Category, Tag, Vendor, Product, ProductReview, ProductImage, CartOrder, CartOrderItem, Wishlist, Address

def default(request):
    categories = Category.objects.all()
    address = None
    if request.user.is_authenticated:
        try:
            address = Address.objects.get(user=request.user)
        except Address.DoesNotExist:
            address = None
    return {
        'categories': categories,
        'address': address,
    }