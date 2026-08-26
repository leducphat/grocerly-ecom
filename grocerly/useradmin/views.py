from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext as _

from django.db.models import Count

from core.models import STATUS, STATUS_CHOICES, CartOrder, CartOrderItem, Product, Category, ProductReview, ProductImage, Vendor
from userauths.models import Profile, User
from useradmin.forms import AddProductForm
from useradmin.decorators import admin_required

import datetime


# Không có bước duyệt: nhân viên tự quyết trạng thái bằng nút bấm (ADR-0002).
# Giá trị đến từ client nên phải qua whitelist, không gán thẳng vào model.
PRODUCT_STATUS_ACTIONS = {
    'save_draft': 'draft',
    'publish': 'published',
    'disable': 'disabled',
}


def resolve_product_status(request, default):
    """Đổi nút bấm thành `product_status`; nút lạ hoặc thiếu thì giữ `default`."""
    return PRODUCT_STATUS_ACTIONS.get(request.POST.get('action'), default)


@admin_required
def dashboard(request):
    revenue = CartOrder.objects.filter(paid_status=True).aggregate(price=Sum("price"))
    total_orders_count = CartOrder.objects.all()
    all_products = Product.objects.all()
    all_categories = Category.objects.all()
    new_customers = User.objects.all().order_by("-id")[:6]
    latest_orders = CartOrder.objects.all()

    this_month = datetime.datetime.now().month
    monthly_revenue = CartOrder.objects.filter(paid_status=True, order_date__month=this_month).aggregate(price=Sum("price"))

    from django.db.models.functions import ExtractMonth
    import calendar
    from django.db.models import Count

    revenue_data = CartOrder.objects.filter(paid_status=True).annotate(
        month=ExtractMonth("order_date")
    ).values("month").annotate(total_revenue=Sum("price")).values("month", "total_revenue")
    
    rev_month = []
    rev_total = []
    for i in revenue_data:
        if i["month"]:
            rev_month.append(calendar.month_name[i["month"]])
            rev_total.append(float(i["total_revenue"]))

    context = {
        "monthly_revenue": monthly_revenue,
        "revenue": revenue,
        "all_products": all_products,
        "all_categories": all_categories,
        "new_customers": new_customers,
        "latest_orders": latest_orders,
        "total_orders_count": total_orders_count,
        "rev_month": rev_month,
        "rev_total": rev_total,
    }
    return render(request, "useradmin/dashboard.html", context)

@admin_required
def products(request):
    # Filter "Status" trước đây là UI chết: `<select>` không có `name` và không nằm trong
    # form nào. Vô hại khi mọi sản phẩm đều `published`, nhưng từ khi `draft` là trạng
    # thái thật (ADR-0002) thì nhân viên nhìn cả ba trạng thái lẫn lộn mà không lọc được.
    valid_statuses = {value for value, _label in STATUS}
    selected_status = request.GET.get('status', '')

    all_products = Product.objects.all().order_by('-id')
    if selected_status in valid_statuses:
        all_products = all_products.filter(product_status=selected_status)

    # Đếm trên toàn bộ sản phẩm, không theo bộ lọc đang chọn — nếu không thì chọn xong
    # một trạng thái là các trạng thái khác về 0 và không quay lại được.
    counts = {
        row['product_status']: row['n']
        for row in Product.objects.values('product_status').annotate(n=Count('id'))
    }

    context = {
        "all_products": all_products,
        "all_categories": Category.objects.all(),
        "status_options": [
            {'value': value, 'label': label, 'count': counts.get(value, 0)}
            for value, label in STATUS
        ],
        "selected_status": selected_status if selected_status in valid_statuses else '',
        "total_count": sum(counts.values()),
    }
    return render(request, "useradmin/products.html", context)

from django.http import JsonResponse

@csrf_exempt
@admin_required
def update_stock(request):
    if request.method == "POST":
        pid = request.POST.get("pid")
        stock_count = request.POST.get("stock_count")
        try:
            product = Product.objects.get(p_id=pid)
            product.stock_count = int(stock_count)
            product.save()
            return JsonResponse({"bool": True, "stock_count": product.stock_count})
        except Exception as e:
            return JsonResponse({"bool": False, "error": str(e)})
    return JsonResponse({"bool": False})

@admin_required
def add_product(request):
    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            # Mặc định 'draft': lỡ tay bấm Enter thì sản phẩm chưa lên sàn.
            new_form.product_status = resolve_product_status(request, 'draft')
            if not new_form.vendor:
                new_form.vendor = Vendor.objects.filter(user=request.user).first() or Vendor.objects.first()
            new_form.save()
            form.save_m2m()
            
            # Handle additional images
            additional_images = request.FILES.getlist('additional_images')
            import uuid
            for img in additional_images:
                if img.size > 0:
                    ext = img.name.split('.')[-1] if '.' in img.name else 'jpg'
                    img.name = f"{uuid.uuid4().hex[:10]}.{ext}"
                    ProductImage.objects.create(product=new_form, image=img)
                
            return redirect("useradmin:dashboard-products")
    else:
        form = AddProductForm()
    context = {
        'form':form
    }
    return render(request, "useradmin/add-products.html", context)

@admin_required
def edit_product(request, pid):
    product = Product.objects.get(p_id=pid)

    if request.method == "POST":
        form = AddProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            new_form = form.save(commit=False)
            # `product_status` không nằm trong AddProductForm.fields nên giá trị cũ vẫn
            # còn nguyên ở đây — không bấm nút đổi trạng thái thì giữ nguyên.
            new_form.product_status = resolve_product_status(request, product.product_status)
            new_form.save()
            form.save_m2m()
            
            # Handle additional images
            additional_images = request.FILES.getlist('additional_images')
            import uuid
            for img in additional_images:
                if img.size > 0:
                    ext = img.name.split('.')[-1] if '.' in img.name else 'jpg'
                    img.name = f"{uuid.uuid4().hex[:10]}.{ext}"
                    ProductImage.objects.create(product=new_form, image=img)
                
            # Handle deletion of existing images
            delete_images = request.POST.getlist('delete_images')
            # Lọc bỏ các giá trị rỗng/không hợp lệ để tránh ValueError (ví dụ: 'id' expected a number but got '')
            delete_images = [img_id for img_id in delete_images if str(img_id).strip().isdigit()]
            if delete_images:
                ProductImage.objects.filter(id__in=delete_images, product=new_form).delete()
                
            return redirect("useradmin:dashboard-products")
    else:
        form = AddProductForm(instance=product)
    context = {
        'form':form,
        'product':product,
    }
    return render(request, "useradmin/edit-products.html", context)

def product_has_order_history(product):
    """Sản phẩm này đã từng nằm trong đơn hàng nào chưa?

    Khớp theo **tên** vì `CartOrderItem` chưa có khóa ngoại tới `Product` — nó lưu bản
    sao tĩnh (`item`, `image`, `price`) để hóa đơn không đổi khi sản phẩm bị sửa. Xem
    ADR-0006: khóa ngoại sẽ được thêm ở PLAN bước 2.11, và khi đó hàm này đổi thành tra
    theo khóa ngoại, không còn phải đoán theo tên.

    Khớp theo tên sai được hai chiều, nhưng **hai chiều không nguy hiểm ngang nhau**:

    - Nhầm CÓ (hai sản phẩm trùng tên) → xóa mềm thay vì xóa cứng → dữ liệu còn, khôi
      phục được.
    - Nhầm KHÔNG (sản phẩm đã đổi tên sau khi bán) → xóa cứng → mất bản ghi sản phẩm.

    Hóa đơn của khách **không hỏng** trong cả hai trường hợp, vì `CartOrderItem` giữ bản
    sao riêng. Cái mất là khả năng truy vết ngược từ đơn về sản phẩm gốc.
    """
    return CartOrderItem.objects.filter(item=product.title).exists()


@admin_required
@require_POST
def delete_product(request, pid):
    # Chỉ nhận POST. Trước đây đây là một thẻ `<a href>` thường: xóa sản phẩm chỉ bằng
    # một request GET, nên trình duyệt prefetch link, hay bất kỳ ai dụ được nhân viên
    # click vào một URL, đều xóa được. Thao tác phá hủy phải là POST và phải qua CSRF.
    #
    # Trước đây hàm này gọi thẳng `product.delete()` — mà `SoftDeleteModel` chỉ override
    # `delete()` ở tầng QuerySet (Bẫy #3), nên nó **xóa cứng vô điều kiện**, kể cả sản
    # phẩm đã bán. Hình 30 trong báo cáo đã vẽ sẵn nhánh kiểm tra đơn liên quan;
    # SPEC-GAPS B3 là khoảng cách giữa hình đó và code.
    product = get_object_or_404(Product, p_id=pid)

    if product_has_order_history(product):
        product.soft_delete()
        messages.success(request, _(
            "Product '%(title)s' has order history, so it was hidden instead of erased. "
            "It no longer appears in the store and can be restored from the admin site."
        ) % {'title': product.title})
    else:
        product.hard_delete()
        messages.success(request, _(
            "Product '%(title)s' had no orders and was permanently deleted."
        ) % {'title': product.title})

    return redirect("useradmin:dashboard-products")

@admin_required
def orders(request):
    orders = CartOrder.objects.all()
    context = {
        'orders':orders,
    }
    return render(request, "useradmin/orders.html", context)

@admin_required
def order_detail(request, id):
    order = get_object_or_404(CartOrder, id=id)
    order_items = CartOrderItem.objects.filter(order=order)
    context = {
        'order':order,
        'order_items':order_items,
        # Dựng option từ chính model để dropdown không lệch khỏi giá trị hợp lệ — cùng
        # cách trang sản phẩm đã làm. Trước đây danh sách viết tay và option đầu gửi
        # value="pending", một giá trị không tồn tại trong STATUS_CHOICES.
        'order_status_options': STATUS_CHOICES,
        'order_is_final': order.product_status == FINAL_ORDER_STATUS,
    }
    return render(request, "useradmin/order_detail.html", context)

# Lấy thẳng từ model để danh sách hợp lệ không lệch được — cùng cách `products()` đã làm
# với `STATUS`. Lưu ý STATUS_CHOICES là trạng thái GIAO HÀNG, khác hẳn `STATUS` của
# Product dù hai field cùng tên `product_status` (Bẫy #1).
ORDER_STATUS_VALUES = {value for value, _label in STATUS_CHOICES}
ORDER_STATUS_LABELS = dict(STATUS_CHOICES)

# Đơn đã giao là trạng thái cuối — UC 3.2.20 Exception Flow, SPEC-GAPS A8.
FINAL_ORDER_STATUS = 'delivered'


@admin_required
@require_POST
def change_order_status(request, oid):
    # Bỏ @csrf_exempt: form ở order_detail.html vốn đã có {% csrf_token %}, nên việc tắt
    # CSRF ở đây không phục vụ gì ngoài việc mở cho request từ site khác.
    order = get_object_or_404(CartOrder, oid=oid)
    status = request.POST.get("status")

    # A8 — đơn đã giao thì không đổi trạng thái được nữa. Trước đây chuyển ngược
    # delivered → processing là chuyện bình thường, và nó còn kéo theo lỗi trừ kho hai
    # lần ở đoạn dưới.
    if order.product_status == FINAL_ORDER_STATUS:
        messages.error(request, _(
            "Order %(oid)s was already delivered. Its status can no longer be changed."
        ) % {'oid': order.oid})
        return redirect("useradmin:order_detail", order.id)

    # Giá trị đến từ client nên phải qua whitelist, không gán thẳng vào model —
    # `choices` không được ép ở tầng database.
    #
    # Đây không phải phòng xa: option đầu của dropdown ("Change Order Status") gửi
    # value="pending", mà 'pending' KHÔNG nằm trong STATUS_CHOICES. Bấm Save mà chưa
    # chọn gì là đơn rơi vào trạng thái không hợp lệ.
    if status not in ORDER_STATUS_VALUES:
        messages.error(request, _("Please choose a valid order status."))
        return redirect("useradmin:order_detail", order.id)

    # Trừ kho đúng MỘT lần: chỉ khi đơn chuyển sang `shipped` từ một trạng thái **chưa
    # xuất kho**. Điều kiện cũ (`!= 'shipped'`) coi delivered → shipped là một lần giao
    # mới nên trừ kho lần thứ hai cho cùng một đơn.
    #
    # Không viết `== 'processing'`: production có thể còn đơn mắc kẹt ở giá trị rác
    # 'pending' do chính lỗi dropdown ở trên sinh ra. Những đơn đó **chưa** xuất kho, nên
    # khi nhân viên cứu chúng về `shipped` thì vẫn phải trừ kho bình thường.
    already_fulfilled = ('shipped', FINAL_ORDER_STATUS)
    if status == 'shipped' and order.product_status not in already_fulfilled:
        for item in CartOrderItem.objects.filter(order=order):
            # Khớp theo tên vì CartOrderItem chưa có khóa ngoại — nợ kỹ thuật #6,
            # sẽ hết sau PLAN bước 2.11 (ADR-0006).
            product = Product.objects.filter(title=item.item).first()
            if product and product.stock_count is not None:
                product.stock_count = max(0, product.stock_count - item.quantity)
                product.save(update_fields=['stock_count'])

    # Đơn COD được coi là đã thu tiền khi giao tới tay khách.
    if status == FINAL_ORDER_STATUS and order.payment_method == 'cod':
        order.paid_status = True

    order.product_status = status
    order.save()

    messages.success(request, _("Order status changed to %(status)s.") % {
        'status': ORDER_STATUS_LABELS[status],
    })
    return redirect("useradmin:order_detail", order.id)

@admin_required
def shop_page(request):
    products = Product.objects.filter(user=request.user)
    revenue = CartOrder.objects.filter(paid_status=True).aggregate(price=Sum("price"))
    total_sales = CartOrderItem.objects.filter(order__paid_status=True).aggregate(qty=Sum("quantity"))

    context = {
        'products':products,
        'revenue':revenue,
        'total_sales':total_sales,
    }
    return render(request, "useradmin/shop_page.html", context)

@admin_required
def reviews(request):
    reviews = ProductReview.objects.all()
    context = {
        'reviews':reviews,
    }
    return render(request, "useradmin/reviews.html", context)

@admin_required
def settings(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == "POST":
        image = request.FILES.get("image")
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        bio = request.POST.get("bio")
        address = request.POST.get("address")
        country = request.POST.get("country")
        
        if image != None:
            profile.image = image
        profile.full_name = full_name
        profile.phone = phone
        profile.bio = bio
        profile.address = address
        profile.country = country

        profile.save()
        messages.success(request, "Profile Updated Successfully")
        return redirect("useradmin:settings")
    
    context = {
        'profile':profile,
    }
    return render(request, "useradmin/settings.html", context)

@admin_required
def change_password(request):
    user = request.user

    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_new_password = request.POST.get("confirm_new_password")

        if confirm_new_password != new_password:
            messages.error(request, "Confirm Password and New Password Does Not Match")
            return redirect("useradmin:change_password")
        
        if check_password(old_password, user.password):
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password Changed Successfully")
            return redirect("useradmin:change_password")
        else:
            messages.error(request, "Old password is not correct")
            return redirect("useradmin:change_password")
    
    return render(request, "useradmin/change_password.html")
