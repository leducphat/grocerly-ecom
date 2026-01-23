from core.models import Category, Tag, Vendor, Product, ProductReview, ProductImage, CartOrder, CartOrderItem, Wishlist, Address

def default(request):
    categories = Category.objects.all()
    address = Address.objects.get(user=request.user)
    return {
        'categories': categories,
        'address': address,
    }