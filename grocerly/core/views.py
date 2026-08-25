from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Avg, Count, Min, Max
from django.db.models.functions import ExtractMonth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.core import serializers
from django.utils.translation import gettext as _
from taggit.models import Tag

import calendar
from core.vnpay import vnpay
from datetime import datetime
from django.utils import timezone
from zoneinfo import ZoneInfo

from core.models import (
    RATING,
    Category, Vendor, Product, ProductReview, ProductImage,
    CartOrder, CartOrderItem, Wishlist, Address, Coupon,
)
from core.forms import ProductReviewForm
from userauths.models import Profile


import re

def safe_float(val, default=0.0):
    try:
        if val is None:
            return default
        val_str = str(val).replace('₫', '').replace('VND', '').replace('$', '').strip()
        
        if re.match(r'^\d{1,3}(\.\d{3})+$', val_str):
            val_str = val_str.replace('.', '')
            
        if re.match(r'^\d{1,3}(,\d{3})+$', val_str):
            val_str = val_str.replace(',', '')
            
        val_str = re.sub(r'[^\d.,]', '', val_str)
        if not val_str:
            return default
            
        val_str = val_str.replace(',', '.')
        return float(val_str)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=1):
    try:
        return int(safe_float(val, default))
    except (ValueError, TypeError):
        return default


def product_image_url(product):
    """URL ảnh sản phẩm, trả chuỗi rỗng nếu file ảnh không tồn tại."""
    try:
        return product.image.url
    except (ValueError, AttributeError):
        return ''



# Create your views here.
def index(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        elif request.user.is_staff:
            return redirect('useradmin:dashboard')
            
    products = Product.objects.published().order_by('-id')
    categories = Category.objects.all()
    deals_products = Product.objects.published().filter(featured=True).order_by('-id')[:4]
    new_products_sidebar = Product.objects.published().order_by('-date')[:3]

    context = {
        'products': products,
        'categories': categories,
        'deals_products': deals_products,
        'new_products_sidebar': new_products_sidebar,
    }

    return render(request, 'core/index.html', context)


def category_list_view(request):
    categories = Category.objects.all()

    context = {
        'categories': categories
    }

    return render(request, 'core/category-list.html', context)


def product_list_view(request):
    products = Product.objects.published().order_by('-id')
    tags = Tag.objects.all().order_by('-id')[:6]
    categories = Category.objects.all().order_by('title')
    vendors = Vendor.objects.all().order_by('name')
    deals_products = Product.objects.published().filter(featured=True).order_by('-id')[:4]

    price_range = products.aggregate(min_price=Min('price'), max_price=Max('price'))

    context = {
        'products': products,
        'tags': tags,
        'categories': categories,
        'vendors': vendors,
        'deals_products': deals_products,
        'product_count': products.count(),
        'min_price': price_range.get('min_price') or 0,
        'max_price': price_range.get('max_price') or 0,
    }

    return render(request, 'core/product-list.html', context)


def category_product_list_view(request, c_id):
    category = Category.objects.get(c_id=c_id)
    products = Product.objects.published().filter(category=category).order_by('-id')

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
    products = Product.objects.published().filter(vendor=vendor).order_by('-id')
    context = {
        'vendor': vendor,
        'products': products
    }

    return render(request, 'core/vendor-detail.html', context)


def product_detail_view(request, p_id):
    product = get_object_or_404(Product, p_id=p_id)
    images = product.p_image.all()
    related_products = Product.objects.published().filter(category=product.category).exclude(p_id=p_id).order_by('-id')[:4]

    # Getting all reviews related to the product
    reviews = ProductReview.objects.filter(product=product).order_by('-date')

    # Getting average review rating
    average_rating = ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))

    total_reviews = reviews.count()
    rating_5 = int((reviews.filter(rating=5).count() / total_reviews) * 100) if total_reviews > 0 else 0
    rating_4 = int((reviews.filter(rating=4).count() / total_reviews) * 100) if total_reviews > 0 else 0
    rating_3 = int((reviews.filter(rating=3).count() / total_reviews) * 100) if total_reviews > 0 else 0
    rating_2 = int((reviews.filter(rating=2).count() / total_reviews) * 100) if total_reviews > 0 else 0
    rating_1 = int((reviews.filter(rating=1).count() / total_reviews) * 100) if total_reviews > 0 else 0

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
        'rating_5': rating_5,
        'rating_4': rating_4,
        'rating_3': rating_3,
        'rating_2': rating_2,
        'rating_1': rating_1,
    }

    return render(request, 'core/product-detail.html', context)


def tag_list(request, tag_slug=None):
    products = Product.objects.published().order_by('-id')

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        'products': products,
        'tag': tag,
    }

    return render(request, 'core/tag.html', context)


@login_required
def validated_review_payload(request):
    """Đọc `review`/`rating` từ POST. Trả `(payload, None)` hoặc `(None, JsonResponse lỗi)`.

    Dùng chung cho thêm và sửa đánh giá để hai đường không lệch quy tắc kiểm tra.
    """
    review_text = (request.POST.get('review') or '').strip()
    if not review_text:
        return None, JsonResponse({'bool': False, 'error': _("Please write a review.")}, status=400)

    valid_ratings = [str(value) for value, _label in RATING]
    rating = request.POST.get('rating')
    if rating not in valid_ratings:
        return None, JsonResponse({'bool': False, 'error': _("Please choose a rating.")}, status=400)

    return {'review': review_text, 'rating': rating}, None


def average_rating_for(product):
    return ProductReview.objects.filter(product=product).aggregate(rating=Avg('rating'))


def own_review_or_none(request, review_id):
    """Đánh giá của **chính** người đang đăng nhập, hoặc None.

    Lọc `user` ngay trong truy vấn thay vì kiểm sau: đánh giá của người khác trả 404 y
    như đánh giá không tồn tại, không lộ ra là nó có thật.
    """
    return ProductReview.objects.filter(pk=review_id, user=request.user).first()


@login_required
def ajax_edit_review(request, review_id):
    if request.method != "POST":
        return JsonResponse({'bool': False, 'error': _("Invalid request.")}, status=405)

    review = own_review_or_none(request, review_id)
    if review is None:
        return JsonResponse({'bool': False, 'error': _("Review not found.")}, status=404)

    payload, error = validated_review_payload(request)
    if error is not None:
        return error

    review.review = payload['review']
    review.rating = payload['rating']
    review.save(update_fields=['review', 'rating'])

    return JsonResponse({
        'bool': True,
        'context': {
            'user': review.user.username,
            'review': review.review,
            'rating': review.rating,
        },
        'average_reviews': average_rating_for(review.product),
    })


@login_required
def ajax_delete_review(request, review_id):
    if request.method != "POST":
        return JsonResponse({'bool': False, 'error': _("Invalid request.")}, status=405)

    review = own_review_or_none(request, review_id)
    if review is None:
        return JsonResponse({'bool': False, 'error': _("Review not found.")}, status=404)

    product = review.product
    review.delete()

    return JsonResponse({
        'bool': True,
        'average_reviews': average_rating_for(product),
    })


@login_required
def ajax_add_review(request, p_id):
    # Chốt chặn cũ chỉ nằm ở context 'make_review' của template nên POST thẳng vào đây
    # là bỏ qua được: khách chưa đăng nhập gây 500, user đã đăng nhập spam review vô hạn.
    if request.method != "POST":
        return JsonResponse({'bool': False, 'error': _("Invalid request.")}, status=405)

    product = get_object_or_404(Product, pk=p_id)
    user = request.user

    if ProductReview.objects.filter(user=user, product=product).exists():
        return JsonResponse({
            'bool': False,
            'error': _("You have already reviewed this product."),
        }, status=400)

    payload, error = validated_review_payload(request)
    if error is not None:
        return error

    review_text = payload['review']
    rating = payload['rating']

    ProductReview.objects.create(
        user=user,
        product=product,
        review=review_text,
        rating=rating,
    )

    context = {
        'user': user.username,
        'review': review_text,
        'rating': rating,
    }

    return JsonResponse({
        'bool': True,
        'context': context,
        'average_reviews': average_rating_for(product),
    })


# ======================== Search ========================

def search_view(request):
    query = request.GET.get("q")
    products = Product.objects.published().filter(title__icontains=query).order_by('-date')

    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'core/search.html', context)


def filter_product(request):
    category_ids = [c for c in (request.GET.getlist("category") + request.GET.getlist("category[]")) if c.isdigit()]
    vendor_ids = [v for v in (request.GET.getlist("vendor") + request.GET.getlist("vendor[]")) if v.isdigit()]
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    products = Product.objects.published().order_by('-id').distinct()

    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except (TypeError, ValueError):
            pass

    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except (TypeError, ValueError):
            pass

    if category_ids:
        products = products.filter(category__id__in=category_ids).distinct()

    if vendor_ids:
        products = products.filter(vendor__id__in=vendor_ids).distinct()

    data = render_to_string("core/async/product-list.html", {"products": products}, request=request)
    return JsonResponse({
        "data": data,
        "count": products.count(),
    })


# ======================== Cart (Session-based) ========================

def add_to_cart(request):
    # Client chỉ được gửi 'id' và 'qty'. Tên, giá, ảnh đều đọc lại từ database:
    # tin giá từ query string cho phép mua hàng 500.000đ với giá 1đ (SECURITY.md S-02).
    product_id = str(request.GET.get('id', '')).strip()
    if not product_id.isdigit():
        return JsonResponse({'error': _("Invalid product.")}, status=400)

    product = Product.objects.published().filter(pk=int(product_id)).first()
    if product is None:
        return JsonResponse({'error': _("This product is no longer on sale.")}, status=404)

    qty = max(1, safe_int(request.GET.get('qty')))

    if product.stock_count is not None and qty > product.stock_count:
        return JsonResponse({
            'error': _("Only %(count)s item(s) left in stock.") % {'count': product.stock_count},
            'stock_count': product.stock_count,
        }, status=400)

    cart_data = request.session.get('cart_data_obj', {})
    cart_data[product_id] = {
        'title': product.title,
        'qty': qty,
        'price': float(product.price),
        'image': product_image_url(product),
        'pid': product.p_id,
    }
    request.session['cart_data_obj'] = cart_data

    return JsonResponse({
        'data': request.session['cart_data_obj'],
        'totalcartitems': len(request.session['cart_data_obj']),
    })


def cart_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            item['qty'] = safe_int(item.get('qty'))
            item['price'] = safe_float(item.get('price'))
            cart_total_amount += item['qty'] * item['price']
        request.session.modified = True
        return render(request, 'core/cart.html', {
            'cart_data': request.session['cart_data_obj'],
            'totalcartitems': len(request.session['cart_data_obj']),
            'cart_total_amount': cart_total_amount,
        })
    else:
        messages.warning(request, "Your cart is empty")
        return redirect("core:index")


@login_required
def checkout_info_view(request):
    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            item['qty'] = safe_int(item.get('qty'))
            item['price'] = safe_float(item.get('price'))
            cart_total_amount += item['qty'] * item['price']
        request.session.modified = True
        return render(request, 'core/checkout-info.html', {
            'cart_data': request.session['cart_data_obj'],
            'totalcartitems': len(request.session['cart_data_obj']),
            'cart_total_amount': cart_total_amount,
        })
    else:
        pending_order = _get_pending_order_from_session(request)
        if pending_order:
            messages.info(request, "You have a pending checkout. Please complete payment.")
            return redirect('core:checkout', pending_order.oid)

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
            item['qty'] = safe_int(item.get('qty'))
            item['price'] = safe_float(item.get('price'))
            cart_total_amount += item['qty'] * item['price']
        request.session.modified = True

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
    product_id = str(request.GET.get('id', '')).strip()
    qty = max(1, safe_int(request.GET.get('qty')))

    # Chặn sửa số lượng vượt tồn kho (UC 3.2.6 Exception Flow). Thiếu bước này thì chốt
    # chặn tồn kho ở add_to_cart vô nghĩa: thêm 1 rồi update lên 999.
    if product_id.isdigit():
        product = Product.objects.filter(pk=int(product_id)).first()
        if product is not None and product.stock_count is not None and qty > product.stock_count:
            return JsonResponse({
                'error': _("Only %(count)s item(s) left in stock.") % {'count': product.stock_count},
                'stock_count': product.stock_count,
            }, status=400)

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[product_id]['qty'] = qty
            request.session['cart_data_obj'] = cart_data

    cart_total_amount = 0
    if 'cart_data_obj' in request.session:
        for p_id, item in request.session['cart_data_obj'].items():
            item['qty'] = safe_int(item.get('qty'))
            item['price'] = safe_float(item.get('price'))
            cart_total_amount += item['qty'] * item['price']
        request.session.modified = True

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


def _get_pending_order_from_session(request):
    pending_oid = request.session.get('pending_order_oid')
    if not pending_oid:
        return None

    if request.user.is_authenticated:
        return CartOrder.objects.filter(
            oid=pending_oid,
            user=request.user,
            paid_status=False,
        ).first()

    return None


def _get_checkout_order_or_none(request, oid):
    if request.user.is_authenticated:
        return CartOrder.objects.filter(oid=oid, user=request.user).first()
    return None

@login_required
def save_checkout_info(request):
    total_amount = 0

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        country = request.POST.get("country")

        if not full_name or not email or not address:
            messages.error(request, "Please provide Full Name, Email, and Address to continue.")
            return redirect("core:checkout-info")

        if 'cart_data_obj' in request.session:
            for p_id, item in request.session['cart_data_obj'].items():
                total_amount += safe_int(item.get('qty')) * safe_float(item.get('price'))

            order = _get_pending_order_from_session(request)

            if order:
                order.price = total_amount
                order.full_name = full_name
                order.email = email
                order.phone = mobile
                order.address = address
                order.city = city
                order.state = state
                order.country = country
                order.saved = 0
                order.coupons.clear()
                order.save()
                CartOrderItem.objects.filter(order=order).delete()
            else:
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
                CartOrderItem.objects.create(
                    order=order,
                    invoice_no="INVOICE_NO-" + str(order.id),
                    item=item['title'],
                    image=item['image'],
                    quantity=safe_int(item.get('qty')),
                    price=safe_float(item.get('price')),
                    total=float(safe_int(item.get('qty'))) * safe_float(item.get('price')),
                )

            request.session['pending_order_oid'] = str(order.oid)

            return redirect("core:checkout", order.oid)

    return redirect("core:index")


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def vnpay_payment(request, oid):
    order = _get_checkout_order_or_none(request, oid)
    if not order:
        messages.warning(request, "Order not found. Please start checkout again.")
        return redirect("core:checkout-info")

    if order.paid_status:
        messages.info(request, "This order has already been paid.")
        return redirect("core:payment-completed", order.oid)
        
    order.payment_method = 'online' # vnpay is an online method
    order.product_status = 'processing'
    order.save(update_fields=['payment_method', 'product_status'])
    
    import time
    amount = int(order.price) * 100 # VNPAY expects amount * 100
    order_desc = f"Thanh_toan_don_hang_{order.oid}"
    txn_ref = f"{order.oid}-{int(time.time())}"

    vnp = vnpay()
    vnp.requestData['vnp_Version'] = '2.1.0'
    vnp.requestData['vnp_Command'] = 'pay'
    vnp.requestData['vnp_TmnCode'] = settings.VNPAY_TMN_CODE
    vnp.requestData['vnp_Amount'] = str(amount)
    vnp.requestData['vnp_CurrCode'] = 'VND'
    vnp.requestData['vnp_TxnRef'] = txn_ref
    vnp.requestData['vnp_OrderInfo'] = order_desc
    vnp.requestData['vnp_OrderType'] = 'billpayment'
    vnp.requestData['vnp_Locale'] = 'vn'
    
    vnp.requestData['vnp_ReturnUrl'] = request.build_absolute_uri(reverse("core:vnpay_return"))
    vnp.requestData['vnp_IpAddr'] = get_client_ip(request)
    
    vn_tz = ZoneInfo('Asia/Ho_Chi_Minh')
    now = timezone.now().astimezone(vn_tz)
    vnp.requestData['vnp_CreateDate'] = now.strftime('%Y%m%d%H%M%S')
    
    vnpay_payment_url = vnp.get_payment_url(settings.VNPAY_PAYMENT_URL, settings.VNPAY_HASH_SECRET)
    
    return redirect(vnpay_payment_url)

def vnpay_return(request):
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        txn_ref = inputData.get('vnp_TxnRef')
        order_id = txn_ref.split('-')[0] if txn_ref else None
        vnp_ResponseCode = inputData.get('vnp_ResponseCode')
        
        if vnp.validate_response(settings.VNPAY_HASH_SECRET):
            if vnp_ResponseCode == "00":
                try:
                    order = CartOrder.objects.get(oid=order_id)
                    order.paid_status = True
                    order.save()
                    
                    if 'cart_data_obj' in request.session:
                        del request.session['cart_data_obj']
                        
                    pending_oid = request.session.get('pending_order_oid')
                    if pending_oid and str(order.oid) == str(pending_oid):
                        del request.session['pending_order_oid']
                        
                    messages.success(request, "Thanh toán VNPay thành công!")
                    return redirect("core:payment-completed", order.oid)
                except CartOrder.DoesNotExist:
                    messages.error(request, "Đơn hàng không tồn tại.")
                    return redirect("core:index")
            else:
                messages.error(request, f"Lỗi thanh toán VNPay. Mã lỗi: {vnp_ResponseCode}")
                return redirect("core:payment-failed")
        else:
            messages.error(request, "Sai chữ ký bảo mật (Invalid signature).")
            return redirect("core:payment-failed")
    return redirect("core:index")

@csrf_exempt
def vnpay_ipn(request):
    inputData = request.GET
    if inputData:
        vnp = vnpay()
        vnp.responseData = inputData.dict()
        txn_ref = inputData.get('vnp_TxnRef')
        order_id = txn_ref.split('-')[0] if txn_ref else None
        amount = inputData.get('vnp_Amount')
        vnp_ResponseCode = inputData.get('vnp_ResponseCode')
        
        if vnp.validate_response(settings.VNPAY_HASH_SECRET):
            try:
                order = CartOrder.objects.get(oid=order_id)
                if int(amount) != int(order.price) * 100:
                    return JsonResponse({'RspCode': '04', 'Message': 'Invalid amount'})
                    
                if order.paid_status:
                    return JsonResponse({'RspCode': '02', 'Message': 'Order already confirmed'})
                    
                if vnp_ResponseCode == '00':
                    order.paid_status = True
                    order.save()
                    return JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})
                else:
                    return JsonResponse({'RspCode': '00', 'Message': 'Confirm Success'})
            except CartOrder.DoesNotExist:
                return JsonResponse({'RspCode': '01', 'Message': 'Order not found'})
        else:
            return JsonResponse({'RspCode': '97', 'Message': 'Invalid signature'})
    return JsonResponse({'RspCode': '99', 'Message': 'Unknown error'})


@login_required
def place_cod_order(request, oid):
    if request.method != "POST":
        return redirect("core:checkout", oid)

    order = _get_checkout_order_or_none(request, oid)
    if not order:
        messages.warning(request, "Order not found. Please start checkout again.")
        return redirect("core:checkout-info")

    if order.paid_status:
        messages.info(request, "This order has already been paid.")
        return redirect("core:payment-completed", order.oid)

    order.payment_method = 'cod'
    order.product_status = 'processing'
    order.save(update_fields=['payment_method', 'product_status'])

    if 'cart_data_obj' in request.session:
        del request.session['cart_data_obj']

    messages.success(request, "Order placed with Cash on Delivery.")
    return redirect("core:payment-completed", order.oid)


@login_required
def checkout(request, oid):
    order = _get_checkout_order_or_none(request, oid)
    if not order:
        messages.warning(request, "Checkout session not found. Please continue from checkout info.")
        return redirect("core:checkout-info")

    order_items = CartOrderItem.objects.filter(order=order)

    if order.paid_status:
        messages.info(request, "This order has already been paid.")
        return redirect("core:payment-completed", order.oid)

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
    }
    return render(request, 'core/checkout.html', context)


@login_required
def payment_completed_view(request, oid):
    order = _get_checkout_order_or_none(request, oid)
    if not order:
        messages.warning(request, "Order not found. Please start checkout again.")
        return redirect("core:checkout-info")

    # View này chỉ HIỂN THỊ kết quả, không được ghi paid_status (SECURITY.md S-01):
    # gõ thẳng URL này sẽ biến đơn chưa trả thành đã trả. paid_status chỉ được đặt bởi
    # vnpay_return / vnpay_ipn (online, đã kiểm chữ ký) hoặc khi nhân viên chuyển đơn
    # COD sang 'delivered'.
    if order.payment_method == 'online' and not order.paid_status:
        messages.warning(request, _("This order has not been paid yet. Please complete the payment."))
        return redirect("core:checkout", order.oid)

    if 'cart_data_obj' in request.session:
        del request.session['cart_data_obj']

    pending_oid = request.session.get('pending_order_oid')
    if pending_oid and str(order.oid) == str(pending_oid):
        del request.session['pending_order_oid']

    context = {
        'order': order,
    }
    return render(request, 'core/payment-completed.html', context)


@login_required
def payment_failed_view(request):
    pending_order = _get_pending_order_from_session(request)

    return render(request, 'core/payment-failed.html', {
        'pending_order': pending_order,
    })


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

def add_to_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({"bool": False, "error": "Vui lòng đăng nhập để thêm vào Wishlist!"})

    product_id = request.GET.get('id')
    product = Product.objects.get(id=product_id)

    wishlist_qs = Wishlist.objects.filter(product=product, user=request.user)

    if wishlist_qs.exists():
        wishlist_qs.delete()
        added = False
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product,
        )
        added = True
        
    total_wishlist = Wishlist.objects.filter(user=request.user).count()
    context = {"bool": True, "added": added, "total_wishlist_items": total_wishlist}

    return JsonResponse(context)


def remove_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({"bool": False, "error": "Vui lòng đăng nhập để sử dụng Wishlist!"})

    pid = request.GET.get('id')
    try:
        wishlist_d = Wishlist.objects.get(id=pid, user=request.user)
        wishlist_d.delete()
    except Wishlist.DoesNotExist:
        pass

    wishlist = Wishlist.objects.filter(user=request.user)
    total_wishlist = wishlist.count()

    context = {
        "bool": True,
        "w": wishlist,
    }
    wishlist_json = serializers.serialize('json', wishlist)
    t = render_to_string('core/async/wishlist-list.html', context, request=request)
    return JsonResponse({'data': t, 'w': wishlist_json, 'total_wishlist_items': total_wishlist})

# ======================== Static Pages & Contact ========================
from userauths.models import ContactUs

def contact(request):
    return render(request, "core/contact.html")

def ajax_contact_form(request):
    full_name = request.GET.get('full_name')
    email = request.GET.get('email')
    phone = request.GET.get('phone')
    subject = request.GET.get('subject')
    message = request.GET.get('message')

    ContactUs.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        subject=subject,
        message=message,
    )

    data = {
        "bool": True,
        "message": "Message Sent Successfully"
    }
    return JsonResponse({"data": data})

def about_us(request):
    return render(request, "core/about_us.html")

def purchase_guide(request):
    return render(request, "core/purchase_guide.html")

def privacy_policy(request):
    return render(request, "core/privacy_policy.html")

def terms_of_service(request):
    return render(request, "core/terms_of_service.html")

def coming_soon(request):
    return render(request, "core/coming-soon.html")