from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Avg, Count
from django.db.models.functions import ExtractMonth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.core import serializers
from taggit.models import Tag

import calendar
import stripe

from core.models import (
    Category, Vendor, Product, ProductReview, ProductImage,
    CartOrder, CartOrderItem, Wishlist, Address, Coupon,
)
from core.forms import ProductReviewForm
from userauths.models import Profile


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
    tags = Tag.objects.all().order_by('-id')[:6]

    context = {
        'products': products,
        'tags': tags,
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
    images = product.p_image.all()
    related_products = Product.objects.filter(category=product.category, product_status='published').exclude(p_id=p_id).order_by('-id')[:4]

    # Getting all reviews related to the product
    reviews = ProductReview.objects.filter(product=product).order_by('-date')

    # Getting average review rating
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))

    # Product Review form
    review_form = ProductReviewForm()

    make_review = True

    if request.user.is_authenticated:
        user_review_count = ProductReview.objects.filter(user=request.user, product=product).count()
        if user_review_count > 0:
            make_review = False

    context = {
        'p': product,
        'p_image': images,
        'related_products': related_products,
        'reviews': reviews,
        'average_rating': average_rating,
        'review_form': review_form,
        'make_review': make_review,
    }

    return render(request, 'core/product-detail.html', context)


def tag_list(request, tag_slug=None):
    products = Product.objects.filter(product_status='published').order_by('-id')

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        'products': products,
        'tag': tag,
    }

    return render(request, 'core/tag.html', context)


def ajax_add_review(request, p_id):
    product = Product.objects.get(pk=p_id)
    user = request.user

    review = ProductReview.objects.create(
        user=user,
        product=product,
        review=request.POST['review'],
        rating=request.POST['rating'],
    )

    context = {
        'user': user.username,
        'review': request.POST['review'],
        'rating': request.POST['rating'],
    }

    average_reviews = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))

    return JsonResponse({
        'bool': True,
        'context': context,
        'average_reviews': average_reviews,
    })


# ======================== Search ========================

def search_view(request):
    query = request.GET.get("q")
    products = Product.objects.filter(title__icontains=query, product_status='published').order_by('-date')

    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'core/search.html', context)


# ======================== Cart (Session-based) ========================

def add_to_cart(request):
    cart_product = {}

    cart_product[str(request.GET['id'])] = {
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
        'image': request.GET['image'],
        'pid': request.GET['pid'],
    }

    if 'cart_data_obj' in request.session:
        if str(request.GET['id']) in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
            cart_data.update(cart_data)
            request.session['cart_data_obj'] = cart_data
        else:
            cart_data = request.session['cart_data_obj']
            cart_data.update(cart_product)
            request.session['cart_data_obj'] = cart_data
    else:
        request.session['cart_data_obj'] = cart_product

    return JsonResponse({
        'data': request.session['cart_data_obj'],
        'totalcartitems': len(request.session['cart_data_obj']),
    })


def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])
        return render(request, 'core/cart.html', {
            'cart_data': request.session['cart_data_obj'],
            'totalcartitems': len(request.session['cart_data_obj']),
            'cart_total_amount': cart_total_amount,
        })
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")


def delete_item_from_cart(request):
    product_id = str(request.GET['id'])
    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            del request.session['cart_data_obj'][product_id]
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {
        'cart_data': request.session['cart_data_obj'],
        'totalcartitems': len(request.session['cart_data_obj']),
        'cart_total_amount': cart_total_amount,
    })
    return JsonResponse({
        'data': context,
        'totalcartitems': len(request.session['cart_data_obj']),
    })


def update_cart(request):
    product_id = str(request.GET['id'])
    product_qty = request.GET['qty']

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[str(request.GET['id'])]['qty'] = product_qty
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            cart_total_amount += int(item['qty']) * float(item['price'])

    context = render_to_string("core/async/cart-list.html", {
        'cart_data': request.session['cart_data_obj'],
        'totalcartitems': len(request.session['cart_data_obj']),
        'cart_total_amount': cart_total_amount,
    })
    return JsonResponse({
        'data': context,
        'totalcartitems': len(request.session['cart_data_obj']),
    })


# ======================== Checkout + Payment ========================

@login_required
def save_checkout_info(request):
    cart_total_amount = 0
    total_amount = 0

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")

        if 'cart_data_obj' in request.session:
            for p_id, item in request.session['cart_data_obj'].items():
                total_amount += int(item['qty']) * float(item['price'])

            order = CartOrder.objects.create(
                user=request.user,
                price=total_amount,
                full_name=full_name,
                email=email,
                phone=mobile,
                address=address,
                city=city,
                state=state,
                country=country,
            )

            for p_id, item in request.session['cart_data_obj'].items():
                cart_total_amount += int(item['qty']) * float(item['price'])

                CartOrderItem.objects.create(
                    order=order,
                    invoice_no="INVOICE_NO-" + str(order.id),
                    item=item['title'],
                    image=item['image'],
                    quantity=int(item['qty']),
                    price=item['price'],
                    total=float(item['qty']) * float(item['price']),
                )

            # Clear the cart after order creation
            del request.session['cart_data_obj']

            return redirect("core:checkout", order.oid)

    return redirect("core:index")


@csrf_exempt
def create_checkout_session(request, oid):
    order = CartOrder.objects.get(oid=oid)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        customer_email=order.email,
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': order.full_name,
                    },
                    'unit_amount': int(order.price * 100),
                },
                'quantity': 1,
            }
        ],
        mode='payment',
        success_url=request.build_absolute_uri(
            reverse("core:payment-completed", args=[order.oid])
        ) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(
            reverse("core:payment-failed")
        ),
    )

    order.paid_status = False
    order.stripe_payment_intent = checkout_session['id']
    order.save()

    return JsonResponse({"sessionId": checkout_session.id})


@login_required
def checkout(request, oid):
    order = CartOrder.objects.get(oid=oid)
    order_items = CartOrderItem.objects.filter(order=order)

    if request.method == "POST":
        code = request.POST.get("code")
        coupon = Coupon.objects.filter(code=code, active=True).first()
        if coupon:
            if coupon in order.coupons.all():
                messages.warning(request, "Coupon already activated")
                return redirect("core:checkout", order.oid)
            else:
                discount = order.price * coupon.discount / 100
                order.coupons.add(coupon)
                order.price -= discount
                order.saved += discount
                order.save()
                messages.success(request, "Coupon Activated")
                return redirect("core:checkout", order.oid)
        else:
            messages.error(request, "Coupon Does Not Exist")

    context = {
        'order': order,
        'order_items': order_items,
        'stripe_publishable_key': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'core/checkout.html', context)


@login_required
def payment_completed_view(request, oid):
    order = CartOrder.objects.get(oid=oid)

    if order.paid_status == False:
        order.paid_status = True
        order.save()

    context = {
        'order': order,
    }
    return render(request, 'core/payment-completed.html', context)


@login_required
def payment_failed_view(request):
    return render(request, 'core/payment-failed.html')


# ======================== Dashboard ========================

@login_required
def customer_dashboard(request):
    orders_list = CartOrder.objects.filter(user=request.user).order_by("-id")
    address = Address.objects.filter(user=request.user)

    # Monthly order chart data
    orders = CartOrder.objects.annotate(
        month=ExtractMonth("order_date")
    ).values("month").annotate(count=Count("id")).values("month", "count")
    month = []
    total_orders = []
    for i in orders:
        month.append(calendar.month_name[i["month"]])
        total_orders.append(i["count"])

    # Handle new address creation
    if request.method == "POST":
        new_address = request.POST.get("address")
        mobile = request.POST.get("mobile")

        Address.objects.create(
            user=request.user,
            address=new_address,
            mobile=mobile,
        )
        messages.success(request, "Address Added Successfully.")
        return redirect("core:dashboard")

    user_profile = Profile.objects.get(user=request.user)

    context = {
        "user_profile": user_profile,
        "orders": orders,
        "orders_list": orders_list,
        "address": address,
        "month": month,
        "total_orders": total_orders,
    }
    return render(request, 'core/dashboard.html', context)


@login_required
def order_detail(request, id):
    order = CartOrder.objects.get(user=request.user, id=id)
    order_items = CartOrderItem.objects.filter(order=order)

    context = {
        "order_items": order_items,
    }
    return render(request, 'core/order-detail.html', context)


# ======================== Address ========================

@login_required
def make_address_default(request):
    id = request.GET['id']
    Address.objects.filter(user=request.user).update(status=False)
    Address.objects.filter(id=id, user=request.user).update(status=True)
    return JsonResponse({"boolean": True})


# ======================== Wishlist ========================

@login_required
def wishlist_view(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    context = {
        "w": wishlist,
    }
    return render(request, "core/wishlist.html", context)


@login_required
def add_to_wishlist(request):
    product_id = request.GET['id']
    product = Product.objects.get(id=product_id)

    wishlist_count = Wishlist.objects.filter(product=product, user=request.user).count()

    if wishlist_count > 0:
        context = {"bool": True}
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product,
        )
        context = {"bool": True}

    return JsonResponse(context)


@login_required
def remove_wishlist(request):
    pid = request.GET['id']
    wishlist = Wishlist.objects.filter(user=request.user)
    wishlist_d = Wishlist.objects.get(id=pid)
    wishlist_d.delete()

    context = {
        "bool": True,
        "w": wishlist,
    }
    wishlist_json = serializers.serialize('json', wishlist)
    t = render_to_string('core/async/wishlist-list.html', context)
    return JsonResponse({'data': t, 'w': wishlist_json})