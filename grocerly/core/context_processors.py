from core.models import Category, Vendor, Product, Wishlist, Address

def default(request):
    categories = Category.objects.all()
    address = None
    wishlist_count = 0

    if request.user.is_authenticated:
        try:
            address = Address.objects.filter(user=request.user, status=True).first()
        except Address.DoesNotExist:
            address = None
        wishlist_count = Wishlist.objects.filter(user=request.user).count()

    # Session-based cart count
    cart_total_items = 0
    if 'cart_data_obj' in request.session:
        cart_total_items = len(request.session['cart_data_obj'])

    return {
        'categories': categories,
        'address': address,
        'wishlist_count': wishlist_count,
        'cart_total_items': cart_total_items,
    }