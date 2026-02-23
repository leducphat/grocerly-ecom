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


def category_list_view(request):
    categories = Category.objects.all()

    context = {
        'categories': categories
    }

    return render(request, 'core/category-list.html', context)


def product_list_view(request):
    products = Product.objects.filter(product_status='published').order_by('-id')

    context = {
        'products': products
    }

    return render(request, 'core/product-list.html', context)


def category_product_list_view(request, c_id):
    category = Category.objects.get(c_id=c_id)
    products = Product.objects.filter(category=category, product_status='published').order_by('-id')

    context = {
        'category': category,
        'products': products
    }

    return render(request, 'core/category-product-list.html', context)


def vendor_list_view(request):
    vendors = Vendor.objects.all()

    context = {
        'vendors': vendors
    }

    return render(request, 'core/vendor-list.html', context)


def vendor_detail_view(request, v_id):
    vendor = Vendor.objects.get(v_id=v_id)
    products = Product.objects.filter(vendor=vendor, product_status='published').order_by('-id')
    context = {
        'vendor': vendor,
        'products': products
    }

    return render(request, 'core/vendor-detail.html', context)


def product_detail_view(request, p_id):
    product = Product.objects.get(p_id=p_id)
    # reviews = ProductReview.objects.filter(product=product, review_status='approved').order_by('-id')
    images = product.p_image.all()
    related_products = Product.objects.filter(category=product.category, product_status='published').exclude(p_id=p_id).order_by('-id')[:4]

    context = {
        'p': product,
        #'reviews': reviews,
        'p_image': images,
        'related_products': related_products
    }

    return render(request, 'core/product-detail.html', context)