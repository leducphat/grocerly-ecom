# Ghi nhận vấn đề bảo mật

> Rà soát ngày 2026-08-20 trên commit `42f6fdb`, cập nhật 2026-08-24. Đây là tài liệu
> nội bộ của dự án, phục vụ việc tự khắc phục.

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

Các mục đã sửa đều có test hồi quy ở [core/tests.py](../grocerly/core/tests.py):

```bash
cd grocerly
python manage.py test core --settings=grocerly.settings_test
```

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
