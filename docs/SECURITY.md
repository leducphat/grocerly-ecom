# Ghi nhận vấn đề bảo mật

> Rà soát ngày 2026-08-20 trên commit `42f6fdb`, cập nhật 2026-08-26. Đây là tài liệu
> nội bộ của dự án, phục vụ việc tự khắc phục.
>
> S-09 đến S-11 đến từ một **lượt rà soát riêng ngày 2026-08-26**, quét mọi endpoint đổi
> trạng thái để tìm chỗ nhận GET hoặc tắt CSRF. Cách làm và cả những phát hiện **bị bác
> bỏ** ghi ở mục [Rà soát 2026-08-26](#rà-soát-2026-08-26--endpoint-đổi-trạng-thái) cuối file.

Báo cáo (mục 1.2.2 — Yêu cầu phi chức năng) cam kết *"mọi giao dịch thanh toán đều được
thực hiện qua các kênh kết nối an toàn"* và *"có cơ chế ngăn chặn hiệu quả các cuộc tấn
công SQL Injection và XSS"*. Django lo phần SQL Injection/XSS/CSRF khá tốt, nhưng các
mục dưới đây là **lỗi logic nghiệp vụ** mà framework không đỡ được.

| Mã | Vấn đề | Mức | Trạng thái |
|---|---|---|---|
| S-01 | Bỏ qua thanh toán bằng cách truy cập URL | 🔴 Nghiêm trọng | ✅ Đã sửa 2026-08-24 |
| S-02 | Giả mạo giá sản phẩm qua query string | 🔴 Nghiêm trọng | ✅ Đã sửa 2026-08-24 |
| S-03 | Endpoint AI không xác thực, không giới hạn tần suất | 🟠 Cao | ✅ Đã sửa 2026-08-25 |
| S-04 | Rò rỉ sản phẩm chưa đăng bán qua API và chatbot | 🟠 Cao | ✅ Đã sửa 2026-08-24 |
| S-05 | `SECRET_KEY` có giá trị mặc định | 🟡 Trung bình | Chưa sửa |
| S-06 | Lộ thông tin đăng nhập production trong báo cáo | 🔴 Nghiêm trọng | Cần đổi mật khẩu sau bảo vệ |
| S-07 | `except:` trần nuốt lỗi ở luồng đăng nhập | 🔵 Thấp | Chưa sửa |
| S-08 | Chốt chặn đánh giá chỉ nằm ở template | 🟠 Cao | ✅ Đã sửa 2026-08-24 |
| S-09 | Form liên hệ ghi database bằng GET không xác thực | 🟠 Cao | ✅ Đã sửa 2026-08-26 |
| S-10 | Các endpoint khác đổi dữ liệu bằng GET | 🟡 Trung bình | Chưa sửa — [PLAN](PLAN.md) bước 2.14 |
| S-11 | Cookie phiên không có cờ `Secure` | 🔵 Thấp | Chưa sửa — [PLAN](PLAN.md) bước 2.14 |

⚠️ **Không mục nào trong bảng này đang được bảo vệ trên production.** Mọi bản vá vẫn nằm
trên `develop`; `main` chậm 28 commit và việc deploy **đã được hoãn có chủ ý** — xem
[PLAN.md](PLAN.md) giai đoạn 1.

Các mục đã sửa đều có test hồi quy. Chạy toàn bộ:

```bash
cd grocerly
python manage.py test --settings=grocerly.settings_test
```

| Mục | Test |
|---|---|
| S-01, S-02, S-08 | [core/tests.py](../grocerly/core/tests.py) |
| S-03, S-04 | [store_api/tests.py](../grocerly/store_api/tests.py) |
| S-09 | [core/test_contact_form.py](../grocerly/core/test_contact_form.py) |

---

## S-01 — Bỏ qua thanh toán bằng cách truy cập URL

> ✅ **Đã sửa 2026-08-24.** `payment_completed_view` không còn ghi `paid_status`; đơn
> online chưa thanh toán bị đá về `/checkout/<oid>/` kèm cảnh báo. Test hồi quy:
> `PaymentCompletedTests` trong [core/tests.py](../grocerly/core/tests.py).

**Vị trí:** `core/views.py` — `payment_completed_view`

```python
if order.payment_method == 'online' and order.paid_status == False:
    order.paid_status = True
    order.save()
```

**Vấn đề:** View đánh dấu đơn hàng **đã thanh toán** chỉ dựa vào việc người dùng truy cập
URL, không hề kiểm tra kết quả trả về từ VNPay.

**Kịch bản khai thác:** Khách tạo đơn → tới bước chọn thanh toán → thay vì bấm VNPay, gõ
thẳng `/payment-completed/<oid>/` trên trình duyệt. Đơn chuyển sang *đã thanh toán* mà
không có đồng nào được chuyển. `oid` lấy được ngay từ URL của bước trước.

**Vì sao tồn tại:** Có lẽ để "chữa cháy" trường hợp `vnpay_return` thất bại. Nhưng
`vnpay_return` (đã kiểm tra chữ ký) và `vnpay_ipn` (đã kiểm tra chữ ký + số tiền) đã làm
đúng việc này rồi — đoạn code trên là dư thừa và phá vỡ toàn bộ vòng bảo vệ.

**Đã sửa:** Bỏ hẳn việc ghi `paid_status` trong view này. View chỉ *hiển thị* kết quả.
Trạng thái thanh toán chỉ được đặt bởi `vnpay_return`/`vnpay_ipn` (online) hoặc khi nhân
viên chuyển đơn COD sang `delivered`.

Luồng thanh toán thành công **không bị ảnh hưởng**: `vnpay_return` đã đặt
`paid_status = True` và `save()` **trước khi** redirect sang `payment-completed`, còn
`place_cod_order` đã đổi `payment_method` sang `'cod'` nên không rơi vào nhánh cảnh báo.

---

## S-02 — Giả mạo giá sản phẩm

> ✅ **Đã sửa 2026-08-24.** `add_to_cart` chỉ còn nhận `id` và `qty`; tên, giá, ảnh đọc
> từ database. Test hồi quy: `AddToCartPriceTamperingTests` trong
> [core/tests.py](../grocerly/core/tests.py).

**Vị trí:** `core/views.py` — `add_to_cart`

```python
cart_product[str(request.GET['id'])] = {
    'title': request.GET['title'],
    'price': safe_float(request.GET.get('price')),   # ← giá do client gửi
    ...
}
```

**Vấn đề:** Tiêu đề và **giá** lấy trực tiếp từ query string. Server không đối chiếu lại
với database. Giá này được dùng suốt: tính tổng giỏ, ghi vào `CartOrder.price`, và cuối
cùng là số tiền gửi sang VNPay.

**Kịch bản khai thác:** Gọi
`/add-to-cart/?id=5&title=X&qty=1&price=1&image=…&pid=…` → mua sản phẩm 500.000đ với
giá 1đ. Không cần công cụ gì ngoài thanh địa chỉ.

**Đã sửa:** Chỉ nhận `id` và `qty` từ client; `title`, `price`, `image` đọc từ
`Product`. Kèm theo ba chốt chặn phát sinh tự nhiên từ việc truy vấn database:

- `id` không phải số → `400`
- sản phẩm không ở trạng thái `published` → `404` (chặn trước một phần [S-04](#s-04--rò-rỉ-sản-phẩm-chưa-đăng-bán) ở phía storefront)
- `qty` vượt `stock_count` → `400`, đóng mục **A5** trong [SPEC-GAPS](SPEC-GAPS.md)

`update_cart` cũng phải kiểm `stock_count`, nếu không chốt chặn ở `add_to_cart` vô nghĩa
— thêm 1 rồi update lên 999 là qua.

Hai JS gọi endpoint này ([base.html](../grocerly/templates/partials/base.html) dòng ~820
cho nút "Add" và ~1116 cho luồng xác nhận của chatbot) vẫn gửi dư `title`/`price`/`image`.
Server bỏ qua nên **không cần sửa template** — nhưng đây là rác nên dọn khi có dịp.

---

## S-03 — Endpoint AI không xác thực, không giới hạn tần suất

> ✅ **Đã sửa 2026-08-25.** Test hồi quy: `ChatThrottleTests`, `ChatInputLimitTests`
> trong [store_api/tests.py](../grocerly/store_api/tests.py).

**Vị trí:** `store_api/views.py` — `ai_chat`

**Vấn đề:** `@api_view(['POST'])` không kèm `permission_classes` hay throttle. Bất kỳ ai
biết URL đều gọi được `/api/v1/chat/` không giới hạn, mỗi lần gọi tiêu tốn hạn ngạch
Gemini của chủ dự án.

Hạn mức miễn phí là **500 tin nhắn/ngày** (chính code đã xử lý thông báo hết quota). Một
script đơn giản làm cạn trong vài phút, khiến chatbot ngừng hoạt động với người dùng thật
— đúng vào lúc demo bảo vệ.

Ngoài ra `history` do client gửi lên được nạp thẳng vào ngữ cảnh hội thoại, cho phép
người dùng tự dựng lịch sử giả để lái hành vi mô hình.

**Đã sửa:** Thêm throttle theo scope trong
[store_api/throttling.py](../grocerly/store_api/throttling.py) —
`ChatAnonThrottle` (đếm theo IP) và `ChatUserThrottle` (đếm theo tài khoản) — cùng giới
hạn `message` ≤ 1000 ký tự và cắt `history` còn 20 lượt gần nhất.
**Không** bắt đăng nhập: khách vãng lai vẫn phải dùng được chatbot theo UC 3.2.15.

Hạn mức đặt ở `settings.REST_FRAMEWORK`: **60/giờ** cho khách vãng lai, **120/giờ** cho
người đã đăng nhập — rộng hơn mức `20/hour` từng đề xuất, có chủ ý: lúc bảo vệ nhiều
người xem cùng ngồi sau một IP (NAT), đặt quá chặt là tự khóa buổi demo.

Response 429 mặc định của DRF là `{"detail": ...}`, mà widget chat chỉ đọc `reply` và
`error` — để nguyên thì người dùng gõ mà **không thấy gì phản hồi**. `chat_exception_handler`
giữ mã 429 (đúng ngữ nghĩa, còn thấy được trong log) nhưng đổi thân response sang
`reply` + `retry_after`, khớp cách view này đã báo lỗi hết quota Gemini.

**Còn lại — hai giới hạn cần biết:**

1. **Không có trần theo ngày trên toàn hệ thống.** Throttle đếm theo từng IP / từng tài
   khoản, nên nhiều IP khác nhau cộng lại vẫn có thể làm cạn 500 tin/ngày. Chặn được
   script một máy — đúng kịch bản khai thác nêu trên — nhưng không chặn được tấn công
   phân tán. Muốn chặn hẳn phải có bộ đếm toàn cục, và nó lại có rủi ro tự khóa demo.
2. **Cắt `history` không phải là chống prompt injection.** Nó giới hạn *lượng* ngữ cảnh
   giả nhét được vào và giữ chi phí mỗi lượt ổn định, nhưng client vẫn tự dựng được lịch
   sử. Chặn hẳn thì phải lưu hội thoại ở server thay vì tin client — thay đổi lớn hơn
   nhiều so với phạm vi mục này.

---

## S-04 — Rò rỉ sản phẩm chưa đăng bán

> ✅ **Đã sửa 2026-08-24** cùng lượt với [ADR-0002](DECISIONS.md). Test hồi quy:
> `store_api/tests.py::DraftLeakTests`.

**Vị trí:** `store_api/views.py` — `ProductListAPI`, `search_products`, `get_bestsellers`

**Vấn đề:** Storefront lọc `product_status='published'`, nhưng `store_api` lọc
`status=True, in_stock=True` — **hai tiêu chí khác nhau**. Sản phẩm ở trạng thái
`draft`/`disabled` vẫn lọt qua API công khai và qua chatbot.

Trước đây tác động thấp vì `add_product` đặt mọi sản phẩm thành `published`. Từ khi
[ADR-0002](DECISIONS.md) được triển khai và `draft` là trạng thái thật, đây là lỗi thấy
được ngay: **chatbot sẽ tư vấn khách mua sản phẩm chưa đăng bán**. Vì vậy hai việc phải
làm cùng một lượt.

**Đã sửa:** Cả ba nơi nay đi qua `Product.objects.published()`. Điều kiện hiển thị được
gom về **một định nghĩa duy nhất** trong `ProductQuerySet.published()`
([core/models.py](../grocerly/core/models.py)) thay cho 12 lần lặp
`filter(product_status='published')` rải khắp `core/views.py` — chính sự lặp lại đó là
lý do `store_api` bị bỏ sót ngay từ đầu.

Hai cờ `status` và `in_stock` **vẫn được giữ** ở `store_api` (`published().filter(status=True,
in_stock=True)`). Việc ba cờ chồng chéo là nợ kỹ thuật riêng, xem
[ARCHITECTURE.md](ARCHITECTURE.md) mục 3.

---

## S-05 — `SECRET_KEY` có giá trị mặc định

**Vị trí:** [grocerly/settings.py:43](../grocerly/grocerly/settings.py#L43)

```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-+bab1(0x...')
```

**Vấn đề:** Nếu production quên set biến môi trường, ứng dụng vẫn khởi động bình thường
với khóa **đã công khai trên GitHub**. `SECRET_KEY` ký session cookie và token reset mật
khẩu → biết khóa là giả mạo được phiên đăng nhập của bất kỳ ai.

`DJANGO_DEBUG` cũng mặc định `'1'` (bật) khi thiếu biến — trang lỗi sẽ phơi bày traceback
và cấu hình.

**Hướng sửa:** Khi `DEBUG=False` mà thiếu `DJANGO_SECRET_KEY` thì `raise ImproperlyConfigured`
thay vì dùng giá trị mặc định. Đảo mặc định của `DJANGO_DEBUG` thành `'0'` (an toàn theo
mặc định).

---

## S-06 — Lộ thông tin đăng nhập production

**Vị trí:** Báo cáo trang 108

Ba tài khoản (Admin superuser, Staff, Customer) được in kèm mật khẩu nguyên văn để giảng
viên tiện chấm. Bản thân việc này hợp lý cho mục đích nộp bài, nhưng:

- Repo GitHub là **public** và được ghi link ngay trang đó
- Site production **đang chạy thật** với đúng các tài khoản này

**Hướng xử lý:** Sau khi bảo vệ xong, đổi mật khẩu cả ba tài khoản. Nếu cần giữ tài khoản
demo cho người xem repo, tạo tài khoản riêng quyền hạn chế, tuyệt đối không phải superuser.

---

## S-07 — `except:` trần ở luồng đăng nhập

**Vị trí:** [userauths/views.py:64](../grocerly/userauths/views.py#L64)

```python
except:
    messages.warning(request, f'User with email {email} does not exist.')
```

**Vấn đề:** `except` trần bắt **mọi** exception — kể cả lỗi kết nối database hay lỗi lập
trình — rồi báo cho người dùng thông điệp sai sự thật ("email không tồn tại"). Lỗi thật
bị nuốt, không log, rất khó chẩn đoán khi sự cố xảy ra lúc demo.

**Hướng sửa:** Bắt đúng `User.DoesNotExist`. Thực ra khối `try` này không cần thiết:
`authenticate()` đã trả `None` khi thông tin sai, nên có thể bỏ hẳn truy vấn
`User.objects.get()` phía trên.

---

## S-08 — Chốt chặn đánh giá chỉ nằm ở template

> ✅ **Đã sửa 2026-08-24.** Test hồi quy: `AddReviewTests` trong
> [core/tests.py](../grocerly/core/tests.py).

**Vị trí:** `core/views.py` — `ajax_add_review`

**Vấn đề:** View tạo `ProductReview` vô điều kiện — không `@login_required`, không kiểm
tra trùng, không kiểm tra `rating` hợp lệ. Điều kiện "mỗi user chỉ đánh giá một lần" chỉ
được tính ở **context của template** (`make_review`), tức là chỉ để *ẩn cái form đi*:

```python
def ajax_add_review(request, p_id):        # không có decorator
    product = Product.objects.get(pk=p_id)
    review = ProductReview.objects.create(
        user=request.user,                  # AnonymousUser → 500
        rating=request.POST['rating'],      # không kiểm giá trị
    )
```

**Kịch bản khai thác:**

1. POST thẳng vào `/vi/ajax-add-review/<id>/` bỏ qua form → một tài khoản spam vô hạn
   đánh giá 5 sao, đẩy điểm trung bình sản phẩm lên tùy ý.
2. Khách **chưa đăng nhập** POST vào cùng URL → `AnonymousUser` không gán được vào khóa
   ngoại `user` → **500**. Nghĩa là đây vừa là lỗ hổng, vừa là lỗi làm sập trang.

**Đã sửa:** Thêm `@login_required`, chỉ nhận `POST`, kiểm tra trùng bằng
`ProductReview.objects.filter(user=..., product=...).exists()`, bắt buộc `review` không
rỗng và `rating` phải nằm trong `RATING`.

**Còn lại:** Điều kiện *"phải mua hàng rồi mới được đánh giá"* (UC 3.2.14 Pre-Conditions,
mục **A2** trong [SPEC-GAPS](SPEC-GAPS.md)) **vẫn chưa được cài** — đây là việc riêng.

**Ghi chú UX (có sẵn từ trước, không do lần sửa này):** form `#commentForm` trong
`product-detail.html` **không có JS xử lý** dù URL tên là `ajax-*` — nó submit cả trang và
người dùng nhìn thấy JSON thô. Sửa được bằng cách thêm một handler `$.ajax` giống các
endpoint giỏ hàng.

---

## S-09 — Form liên hệ ghi database bằng GET không xác thực

> ✅ **Đã sửa 2026-08-26.** Test hồi quy: [core/test_contact_form.py](../grocerly/core/test_contact_form.py).

**Vị trí:** `core/views.py` — `ajax_contact_form`

```python
def ajax_contact_form(request):          # không decorator, không kiểm method
    full_name = request.GET.get('full_name')
    ...
    ContactUs.objects.create(            # ghi database từ query string
        full_name=full_name, email=email, phone=phone, subject=subject, message=message,
    )
```

**Vấn đề:** View ghi thẳng vào database từ query string, **không đăng nhập, không kiểm
method, không giới hạn tần suất**. Vì GET nằm trong nhóm method an toàn nên
`CsrfViewMiddleware` không kiểm token.

Điểm khiến mục này nặng hơn các endpoint GET khác: **nó không cần cookie nào cả**. Chính
sách `SameSite=Lax` của trình duyệt chặn được cookie trên request xuyên site kiểu
`<img>`, nhưng ở đây không có gì để chặn — view không hề đọc `request.user`.

**Kịch bản khai thác:** Kẻ tấn công đặt vào bất kỳ trang nào (blog, chữ ký diễn đàn, bình
luận cho phép ảnh):

```html
<img src="https://.../vi/ajax-contact-form/?full_name=x&email=a@b.c&phone=0&subject=s&message=<10KB rác>">
```

Mỗi lượt xem trang đó là một dòng ghi vào bảng `ContactUs` **trên database production**.
Không cần nạn nhân đăng nhập. `message` là `TextField` **không giới hạn độ dài**, nên đây
vừa là đường spam vừa là đường làm phình storage trên Neon (bẫy #5).

Đã kiểm chứng bằng thực nghiệm: 5 request GET ẩn danh với `enforce_csrf_checks=True` →
5 dòng, đều trả 200.

**Đã sửa:** Đổi sang `@require_POST` và đọc từ `request.POST`. Sau đó CSRF middleware bắt
đầu kiểm token, mà token thì **không lấy được từ origin khác** — vector `<img>` chết hẳn.

Vế client nhỏ hơn tưởng: form ở `contact.html` **vốn đã có** `method="POST"` và
`{% csrf_token %}`, chỉ có JS tự ý ghi đè thành `type: "GET"` và không dùng tới token.

Kèm bốn chốt chặn phát sinh tự nhiên:

| Chốt chặn | Chặn được gì |
|---|---|
| Trường rỗng / chỉ khoảng trắng → 400 | Trước đây `None` xuống cột NOT NULL → `IntegrityError` → **lỗi 500** (`create()` không gọi `full_clean()`) |
| `message` ≤ 2000 ký tự | Model là `TextField` không giới hạn — đây là trần duy nhất |
| Bốn trường ngắn ≤ 200 ký tự | Khớp `max_length`; vượt thì PostgreSQL ném lỗi còn SQLite âm thầm cắt |
| `validate_email` | `ContactUs.email` là `CharField` chứ không phải `EmailField` nên model không kiểm định dạng |

Thêm `error:` callback cho JS — thiếu nó thì mọi mã 400 mới bị nuốt im lặng, đúng vết xe
mà [S-02](#s-02--giả-mạo-giá-sản-phẩm) đã phải vá cho giỏ hàng.

**Còn lại — không có giới hạn tần suất.** POST + CSRF chặn vector drive-by, nhưng người
viết script vẫn lấy được token rồi POST vòng lặp, như mọi form khác. Làm rate limit tử tế
cần **cache dùng chung**; Django mặc định là `LocMemCache` (riêng từng process) nên trên
Render nhiều worker là vô nghĩa. Cùng loại giới hạn mà [S-03](#s-03--endpoint-ai-không-xác-thực-không-giới-hạn-tần-suất) đã ghi.

---

## S-10 — Các endpoint khác đổi dữ liệu bằng GET

**Chưa sửa** — [PLAN.md](PLAN.md) bước 2.14.

Khác S-09 ở một điểm quyết định: **tất cả đều cần phiên đăng nhập**. Mà settings không
đặt `SESSION_COOKIE_SAMESITE` nên Django 5.2 dùng mặc định `Lax`, và `Lax` **không gửi
cookie** trên request xuyên site kiểu `<img>` / `<iframe>` / `fetch`. Vector drive-by vì
vậy đã bị chặn sẵn.

Cái `Lax` **không** chặn là **điều hướng cả trang bằng GET** — tức nạn nhân bấm vào một
link. Đó là mức độ còn lại của nhóm này.

| View | Đổi cái gì |
|---|---|
| `make_address_default` | Đổi địa chỉ giao hàng mặc định của nạn nhân |
| `add_to_wishlist` / `remove_wishlist` | Thêm / xóa mục trong wishlist |
| `logout_view` | Đá nạn nhân khỏi phiên, mất luôn giỏ hàng đang giữ trong session |
| `vnpay_payment` | Lật `payment_method` sang `online` và `product_status` sang `processing` |
| `add_to_cart`, `update_cart`, `delete_item_from_cart`, `payment_completed_view` | Chỉ đụng session của **chính người gửi** — tác động thấp nhất nhóm |

**Hướng sửa:** chuyển sang POST kèm CSRF, giống cách đã làm cho `delete_product` và
`change_order_status`. Phải sửa cả JS gọi chúng.

---

## S-11 — Cookie phiên không có cờ `Secure`

**Chưa sửa** — [PLAN.md](PLAN.md) bước 2.14.

`settings.py` không đặt `SESSION_COOKIE_SECURE` hay `CSRF_COOKIE_SECURE`, nên cả hai là
`False`. Render phục vụ qua HTTPS, nhưng cookie không mang cờ `Secure` thì trình duyệt
vẫn được phép gửi nó qua kết nối HTTP thường nếu có đường nào dẫn tới đó.

**Hướng sửa:** đặt cả hai thành `True` khi `DEBUG=False`. Cùng nhóm với
[S-05](#s-05--secret_key-có-giá-trị-mặc-định), nên làm một lượt ở bước 2.5/2.14.

---

## Rà soát 2026-08-26 — endpoint đổi trạng thái

Một lượt quét riêng, không nhắm vào một lỗi cụ thể mà quét toàn bộ endpoint đổi trạng
thái theo bốn góc nhìn độc lập: theo HTTP method, theo `@csrf_exempt`, theo phân quyền,
và theo link/form trong template. Mỗi phát hiện sau đó được một lượt phản biện độc lập
**cố gắng bác bỏ**.

**46 phát hiện thô → 29 qua được phản biện → 13 mục sau khi gộp trùng.**

Phần đáng ghi lại cho báo cáo không phải con số, mà là **ba phát hiện đã bị bác bỏ** — và
lý do bác bỏ đều chính xác:

| Phát hiện ban đầu | Vì sao sai |
|---|---|
| `update_stock` có `@csrf_exempt` → khai thác được | Decorator có thật, và thực nghiệm cho thấy ghi được `stock_count` mà không cần token. Nhưng tấn công cần cookie staff đi kèm một **POST xuyên site**, mà `SameSite=Lax` **không bao giờ** gửi cookie trên POST xuyên site |
| `vnpay_ipn` có `@csrf_exempt` → lỗ hổng | Decorator là **no-op**: view chỉ đọc `request.GET`, mà Django vốn không kiểm CSRF trên method an toàn. Bỏ decorator không đổi gì |
| `/api/v1/chat/` bỏ qua CSRF vì `@api_view` | `@api_view` có gắn `csrf_exempt` thật, nhưng DRF `SessionAuthentication` **tự ép kiểm CSRF** cho request xác thực bằng session |

Bài học nên đưa vào [PLAN.md](PLAN.md) bước 4.1: đọc code thấy `@csrf_exempt` là **chưa
đủ để kết luận có lỗ hổng**. Phải trả lời thêm: request của kẻ tấn công có mang được
cookie phiên tới không? Với `SameSite=Lax` thì câu trả lời phụ thuộc vào method và vào
việc đó là điều hướng hay subresource — và đó mới là thứ quyết định.
