# Ghi nhận vấn đề bảo mật

> Rà soát ngày 2026-08-20 trên commit `42f6fdb`. Đây là tài liệu nội bộ của dự án,
> phục vụ việc tự khắc phục.

Báo cáo (mục 1.2.2 — Yêu cầu phi chức năng) cam kết *"mọi giao dịch thanh toán đều được
thực hiện qua các kênh kết nối an toàn"* và *"có cơ chế ngăn chặn hiệu quả các cuộc tấn
công SQL Injection và XSS"*. Django lo phần SQL Injection/XSS/CSRF khá tốt, nhưng các
mục dưới đây là **lỗi logic nghiệp vụ** mà framework không đỡ được.

| Mã | Vấn đề | Mức | Trạng thái |
|---|---|---|---|
| S-01 | Bỏ qua thanh toán bằng cách truy cập URL | 🔴 Nghiêm trọng | Chưa sửa |
| S-02 | Giả mạo giá sản phẩm qua query string | 🔴 Nghiêm trọng | Chưa sửa |
| S-03 | Endpoint AI không xác thực, không giới hạn tần suất | 🟠 Cao | Chưa sửa |
| S-04 | Rò rỉ sản phẩm chưa đăng bán qua API và chatbot | 🟠 Cao | Nằm trong [PLAN](PLAN.md) bước 3.1–3.2 |
| S-05 | `SECRET_KEY` có giá trị mặc định | 🟡 Trung bình | Chưa sửa |
| S-06 | Lộ thông tin đăng nhập production trong báo cáo | 🔴 Nghiêm trọng | Cần đổi mật khẩu sau bảo vệ |
| S-07 | `except:` trần nuốt lỗi ở luồng đăng nhập | 🔵 Thấp | Chưa sửa |

---

## S-01 — Bỏ qua thanh toán bằng cách truy cập URL

**Vị trí:** [core/views.py:691](../grocerly/core/views.py#L691) — `payment_completed_view`

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

**Hướng sửa:** Bỏ hẳn việc ghi `paid_status` trong view này. View chỉ nên *hiển thị* kết
quả. Trạng thái thanh toán chỉ được đặt bởi `vnpay_return`/`vnpay_ipn` (online) hoặc khi
nhân viên xác nhận giao hàng (COD).

---

## S-02 — Giả mạo giá sản phẩm

**Vị trí:** [core/views.py:290](../grocerly/core/views.py#L290) — `add_to_cart`

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

**Hướng sửa:** Chỉ nhận `id` (hoặc `pid`) và `qty` từ client. Đọc `title`, `price`,
`image` từ `Product` trong database. Đây cũng là cơ hội kiểm tra luôn `stock_count`
(mục A5 trong [SPEC-GAPS](SPEC-GAPS.md)).

---

## S-03 — Endpoint AI không xác thực, không giới hạn tần suất

**Vị trí:** [store_api/views.py:93](../grocerly/store_api/views.py#L93) — `ai_chat`

**Vấn đề:** `@api_view(['POST'])` không kèm `permission_classes` hay throttle. Bất kỳ ai
biết URL đều gọi được `/api/v1/chat/` không giới hạn, mỗi lần gọi tiêu tốn hạn ngạch
Gemini của chủ dự án.

Hạn mức miễn phí là **500 tin nhắn/ngày** (chính code đã xử lý thông báo hết quota). Một
script đơn giản làm cạn trong vài phút, khiến chatbot ngừng hoạt động với người dùng thật
— đúng vào lúc demo bảo vệ.

Ngoài ra `history` do client gửi lên được nạp thẳng vào ngữ cảnh hội thoại, cho phép
người dùng tự dựng lịch sử giả để lái hành vi mô hình.

**Hướng sửa:** Thêm DRF throttling (`AnonRateThrottle`, ví dụ `20/hour` cho khách vãng
lai), giới hạn độ dài `message` và số lượt `history`. Không nhất thiết phải bắt đăng nhập
— khách vãng lai vẫn cần dùng chatbot theo đặc tả UC 3.2.15.

---

## S-04 — Rò rỉ sản phẩm chưa đăng bán

**Vị trí:** [store_api/views.py:11](../grocerly/store_api/views.py#L11),
[store_api/views.py:21](../grocerly/store_api/views.py#L21), `get_bestsellers`

**Vấn đề:** Storefront lọc `product_status='published'`, nhưng `store_api` lọc
`status=True, in_stock=True` — **hai tiêu chí khác nhau**. Sản phẩm ở trạng thái
`draft`/`disabled` vẫn lọt qua API công khai và qua chatbot.

Hiện tại tác động thấp vì `add_product` đặt mọi sản phẩm thành `published`. Nhưng khi
[ADR-0002](DECISIONS.md) được triển khai và `draft` trở thành trạng thái thật, đây thành
lỗi thấy được ngay: **chatbot sẽ tư vấn khách mua sản phẩm chưa đăng bán**.

**Hướng sửa:** Bổ sung `product_status='published'` vào cả ba nơi. Tốt hơn nữa là gom
điều kiện vào một manager method duy nhất (`Product.objects.published()`) để không tái
diễn — [PLAN](PLAN.md) bước 3.3.

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
