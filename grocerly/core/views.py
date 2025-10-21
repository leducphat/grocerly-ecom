from django.shortcuts import render

from core.models import Category, Tag, Vendor, Product, ProductReview, ProductImage, CartOrder, CartOrderItem, Wishlist, Address


# Create your views here.
def index(request):
    # products = Product.objects.all().order_by('-id')

    products = Product.objects.filter(featured=True, product_status='published').order_by('-id')

    context = {
        'products': products
    }

    return render(request, 'core/index.html', context)


def product_list_view(request):
    products = Product.objects.filter(product_status='published').order_by('-id')

    context = {
        'products': products
    }

    return render(request, 'core/product-list.html', context)