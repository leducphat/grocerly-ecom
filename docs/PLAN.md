# Kế hoạch công việc

> Cập nhật: 2026-08-26 · Nhánh làm việc: `develop`

## Bối cảnh — chuyển từ Tiểu luận sang Khóa luận

**Tiểu luận chuyên ngành đã nộp và có điểm.** Công việc hiện tại là **Khóa luận tốt
nghiệp**, cùng đề tài, **cùng GVHD** (thầy Hoàng Văn Dũng), GVPB chưa biết. Thời hạn:
trên ba tháng.

Bản Tiểu luận (`CLC_CNPM_1_LEDUCPHAT.pdf`) đóng hai vai: **khung format chuẩn của
trường**, và **điểm xuất phát** cho báo cáo mới. Nó không nằm trong repo.

### Nguyên tắc đã đảo chiều

Kế hoạch cũ chạy theo *"code và báo cáo lệch nhau thì sửa bên nào rẻ hơn"* — hợp lý khi
sắp bảo vệ. [ADR-0002](DECISIONS.md) và [ADR-0005](DECISIONS.md) đều ra đời từ áp lực đó.

**KLTN đảo ngược nguyên tắc này.** Có thời gian, cùng GVHD, và cần chứng minh khối lượng
vượt bản trước. Với phần lớn khoảng cách, **viết code để đóng gap tốt hơn sửa báo cáo để
né gap** — vừa đóng khoảng cách, vừa là khối lượng công việc mới.

[ADR-0006](DECISIONS.md) là hệ quả trực tiếp: nó **thay thế ADR-0005** vì lý do loại
phương án ở ADR-0005 hoàn toàn là ràng buộc thời gian của kỳ bảo vệ cũ.

**Ngoại lệ:** [ADR-0002](DECISIONS.md) (bỏ luồng duyệt sản phẩm) **giữ nguyên** — đó là
quyết định nghiệp vụ, không phải cắt giảm vì thiếu thời gian.

---

## Giai đoạn 0 — Chốt khung

- [x] **0.2** Xét lại ADR-0005 → **[ADR-0006](DECISIONS.md)**: thêm khóa ngoại
      `Product` cho `CartOrderItem`
- [x] **0.3** Chốt **[ADR-0003](DECISIONS.md)**: Grocerly là một siêu thị, `Vendor` là
      thương hiệu
- [ ] **0.1** Chốt khung mục lục KLTN — xem [bao-cao/](bao-cao/)
- [ ] **0.4** Mở file gốc xác nhận Hình 4 **đã có** generalization Quản trị viên ─▷
      Người bán chưa. ADR-0001 ghi là còn thiếu, nhưng nhìn hình thì có vẻ đã có

## Giai đoạn 1 — Deploy

- [ ] **1.1** Merge `develop` → `main`, Render tự deploy — **hoãn có chủ ý, 2026-08-26**

`main` đang chậm **50 commit**. Production vẫn chạy code có S-01/S-02 khai thác được —
mọi bản vá đã làm **chưa bảo vệ được gì**.

**Quyết định 2026-08-26: hoãn.** Production đang chạy ổn định và chưa cần demo cho GVHD,
nên người thực hiện đồ án chọn để nguyên và tích lũy thêm thay đổi. Đây là **đánh đổi có
ý thức**, không phải quên: đổi lại là mọi bản vá bảo mật vẫn chỉ nằm trên `develop`.

Hệ quả cần nhớ khi deploy:

- `build.sh` chạy `compilemessages` nên `django.mo` được biên dịch lại — mọi chuỗi tiếng
  Việt thêm từ 2026-08-25 tới nay **chỉ hiện đúng sau bước này** (xem *Bẫy i18n* bên dưới)
- Migration `0006_drop_stripe_payment_intent` sẽ chạy và drop cột thật trên Neon
- Migration `0007_cartorderitem_product` sẽ chạy kèm **backfill dữ liệu**: nó dò lại sản
  phẩm gốc cho từng dòng `CartOrderItem` theo tên. Chỉ ghi vào cột `product`, không đụng
  bản sao tĩnh của hóa đơn — nhưng đây là migration **có ghi dữ liệu** đầu tiên của dự án
  nên đáng soát log sau khi deploy: dòng nào để `NULL` là dòng backfill không dò ra
- Migration `0008_alter_cartorder_product_status` thêm `cancelled` vào `choices`.
  `sqlmigrate` xác nhận **no-op DDL**, không sinh câu lệnh nào — an toàn, giống `0005`
- Migration `0009` thêm ba cột cho `Coupon` (`valid_to`, `usage_limit`, `used_count`).
  Cả ba đều nullable hoặc có default nên **không backfill**: mã đang có giữ nguyên nghĩa
  "không hết hạn, không giới hạn lượt". Trên PostgreSQL đây là `ADD COLUMN` thường
- Migration `0010` đổi `Coupon.discount` sang `PositiveIntegerField`, tức thêm
  `CHECK (discount >= 0)` **lên dữ liệu đang có**. Coupon nào mang `discount` âm sẽ làm
  migration **thất bại giữa chừng** — soát trước bằng
  `Coupon.all_objects.filter(discount__lt=0)`
- Migration `0011` thêm `CartOrder.vnpay_amount`, nullable, `ADD COLUMN` thường, **không
  backfill**. Đơn treo mang `NULL` và đi vào nhánh dự phòng của `vnpay_ipn` ([ADR-0008](DECISIONS.md))
- Trước khi deploy nên soát đơn hàng mắc kẹt ở trạng thái rác:
  `CartOrder.objects.exclude(product_status__in=['processing','shipped','delivered'])`
  — xem bước 2.2

### 🚨 Hai điều kiện bắt buộc trước lần deploy tới

Từ 2026-08-26 việc deploy **không còn là thao tác thuần túy vô hại**. Hai bản vá bảo mật
đặt điều kiện lên môi trường production, và bỏ qua chúng là site không lên được:

1. **`DJANGO_SECRET_KEY` phải có trên Render.** Sau [S-05](SECURITY.md), thiếu biến này
   khi `DEBUG=False` thì `settings.py` ném `ImproperlyConfigured` ngay lúc khởi động. Đó
   đúng là mục đích của bản vá, nhưng phải xác nhận **trước** khi merge.

   Cùng lô đó, `DJANGO_DEBUG` đảo mặc định thành `'0'`. Nếu Render đang **không** đặt
   biến này thì production đang chạy `DEBUG=True` — và sau khi deploy nó sẽ tắt, kéo theo
   `ALLOWED_HOSTS` bắt đầu có hiệu lực thật. Kiểm luôn `DJANGO_ALLOWED_HOSTS` có tên miền
   Render trong đó chưa.

2. **Không coupon nào được mang `discount` âm** — nếu không migration `0010` thất bại.
   Xem gạch đầu dòng ở trên.

### ⚠️ Bẫy i18n — máy dev không có gettext

Máy đang làm việc **không cài gettext**: không có `msgfmt`/`xgettext` trong PATH, trong
`.venv/Scripts/`, trong Git for Windows, và Python bản này không kèm `Tools/i18n/`.
Hệ quả:

- `makemessages` và `compilemessages` **không chạy được ở local**
- `.mo` đang được commit trong repo nhưng lần cuối biên dịch là 2026-06-17, trong khi
  `.po` liên tục được cập nhật → **chuỗi mới không hiện tiếng Việt khi chạy local**
- Từ 2026-08-26, entry `.po` được **thêm bằng tay** kèm script đối chiếu msgid với source
  (rút msgid từ chính file `.py`/template thay vì gõ lại — sai một ký tự là bản dịch hỏng
  im lặng)

Muốn sửa hẳn: `pip install polib` (thuần Python, chỉ dùng lúc dev, **không** thêm vào
`requirements.txt`) rồi compile `.po` → `.mo` bằng script.

## Giai đoạn 2 — Code đóng khoảng cách báo cáo↔code

Xếp theo tỉ lệ giá trị/chi phí. Cột **Neo** là chỗ báo cáo **đã mô tả sẵn** — làm xong
là đóng gap mà không phải sửa báo cáo.

| | Việc | Neo trong báo cáo | Chi phí |
|---|---|---|---|
| ✅ **2.1** | ~~`delete_product` xóa mềm khi có đơn liên quan ([B3](SPEC-GAPS.md))~~ **Xong 2026-08-26** | **Hình 30 đã vẽ sẵn đúng nhánh này** | thấp |
| ✅ **2.2** | ~~Chặn đổi trạng thái khi đơn đã `delivered` ([A8](SPEC-GAPS.md))~~ **Xong 2026-08-26** | UC 3.2.20 Exception Flow | thấp |
| ✅ **2.3** | ~~Làm sạch giỏ hàng ([A4](SPEC-GAPS.md))~~ **Xong 2026-08-26** | UC 3.2.6 Alternate Flow | thấp |
| ✅ **2.4** | ~~Drop cột `stripe_payment_intent`~~ **Migration xong 2026-08-26**, chạy khi deploy | ERD + Bảng 32 **không có** cột này | thấp |
| ✅ **2.5** | ~~`except:` trần ([S-07](SECURITY.md)) + `SECRET_KEY`/`DEBUG` ([S-05](SECURITY.md))~~ **Xong 2026-08-26** | mục 1.2.2 Yêu cầu phi chức năng | thấp |
| ✅ **2.6** | ~~**Tầng unit test** — xem bảng riêng bên dưới~~ **Xong 2026-08-26** | Chương 4 — hai điểm nhấn chưa có test nào | trung bình |
| ✅ **2.7** | ~~Nhập mã vận đơn ở `useradmin` ([A9](SPEC-GAPS.md))~~ **Xong 2026-08-26** | UC 3.2.20 Alternate Flow | trung bình |
| ✅ **2.8** | ~~Phân trang ([A3](SPEC-GAPS.md))~~ **Xong 2026-08-26** | UC 3.2.3 Alternate Flow | trung bình |
| **2.8b** | Đẩy trạng thái bộ lọc lên URL (`replaceState` + khôi phục checkbox) | — | trung bình |
| ✅ **2.9** | ~~Coupon hạn dùng + số lượt ([A6](SPEC-GAPS.md))~~ **Xong 2026-08-26** | UC 3.2.21 | trung bình, có migration |
| ✅ **2.10** | ~~Hủy đơn ([A7](SPEC-GAPS.md))~~ **Xong 2026-08-26** | UC 3.2.25 | trung bình-cao, có migration |
| ✅ **2.11** | ~~**Khóa ngoại `CartOrderItem` → `Product`**~~ **Xong 2026-08-26** | [ADR-0006](DECISIONS.md); vá nợ kỹ thuật #6 | cao, đụng checkout |
| ✅ **2.12** | ~~Điều kiện đã mua mới đánh giá ([A2](SPEC-GAPS.md))~~ **Xong 2026-08-26** | UC 3.2.14 + **Hình 21** | phụ thuộc 2.11 |
| **2.13** | Gửi email hàng loạt ([A10](SPEC-GAPS.md)) | UC 3.2.22 Alternate Flow | cao, cần cấu hình SMTP |
| ✅ **2.14** | ~~Các endpoint đổi dữ liệu bằng GET còn lại ([S-10](SECURITY.md)) + cờ `Secure` cho cookie ([S-11](SECURITY.md))~~ **Xong 2026-08-26** | mục 1.2.2 Yêu cầu phi chức năng | thấp-trung bình |
| ✅ **2.15** | ~~`Coupon.discount` không giới hạn ([S-12](SECURITY.md)) + `vnpay_ipn` so sai số tiền ([S-13](SECURITY.md))~~ **Xong 2026-08-26** | [ADR-0008](DECISIONS.md); UC 3.2.21 cần thêm tiền điều kiện | trung bình, hai migration |

**Ghi chú 2.4:** hôm 2026-08-25 mục này còn treo vì chưa biết báo cáo có mô tả cột đó
không. Đã đọc bản gốc: **ERD Hình 45 và Bảng 32 đều không có** `stripe_payment_intent`.
Nên drop cột làm code **khớp** báo cáo, không phải ngược lại. Đã kiểm production: 11 đơn
hàng, **0 đơn có dữ liệu** ở cột này.

**Ghi chú 2.8b:** phân trang ở bước 2.8 giữ nguyên cơ chế lọc bằng AJAX, nên **URL không
phản ánh trạng thái bộ lọc**: F5 là mất bộ lọc, và không share được link đã lọc. Sửa hẳn
thì phải tách logic lọc thành helper dùng chung cho `product_list_view` và `filter_product`,
đẩy tham số lên querystring, rồi khôi phục trạng thái `checked` cho ba nhóm checkbox. Đây
là phương án **đúng hơn**, không phải phương án ít rủi ro hơn — nên tách ra làm bước riêng.

**Ghi chú 2.11 (sau khi làm xong):** hóa ra còn thẳng hơn dự tính — **khóa của giỏ hàng
chính là khóa chính của sản phẩm** (`add_to_cart` ép `id` phải là chữ số), nên không cần
đi vòng qua `pid`. Backfill dừng ở mức **chỉ nối khi tên ứng với đúng một sản phẩm**;
tên trùng thì để `NULL` chứ không chọn bừa.

### 2.6 — Tầng unit test (mở rộng 2026-08-26)

Ban đầu mục này chỉ là *"unit test VNPay"*. Rà lại thì vấn đề rộng hơn: 49 test có sẵn
**đều là test hồi quy ở mức HTTP** (`django.test.TestCase` + `self.client`), đúng mục
đích của chúng, nhưng **không có tầng unit test nào** dưới đó. Grep xác nhận `safe_float`,
`vnd`, `vnpay.*`, `SoftDeleteModel.*`, hai middleware — tất cả 0 lần xuất hiện trong test.

Thứ tự trong nhóm là đường găng: **2.6a → 2.6d → 2.6f**. **Toàn bộ nhóm 2.6 đã xong
2026-08-26.**

| | Việc | Vì sao | Trạng thái |
|---|---|---|---|
| **2.6a** | `core/vnpay.py` — ký, sort, bỏ giá trị rỗng, URL-encode; `validate_response` với chữ ký đúng/sai/thiếu | Hàm thuần, không DB. Điểm nhấn thứ hai của đề tài mà [C7](SPEC-GAPS.md) ghi là không có TC nào | ✅ **Xong 2026-08-26** — 18 test |
| **2.6b** | `safe_float` / `safe_int` | Nằm trên đường tiền. Hành vi **đang sai so với mô tả** — xem ghi chú dưới | ✅ **Xong 2026-08-26** — 34 test, và hàm đã được sửa |
| **2.6c** | Filter `vnd` / `mul` | Hiển thị trên **mọi** trang có giá | ✅ **Xong 2026-08-26** — 17 test, không phải sửa gì |
| **2.6d** | `SoftDeleteModel` + cascade/restore của `Vendor` | Chốt **Bẫy #3** thành test; là tiền đề của 2.1 | ✅ **Xong 2026-08-26** — 14 test, phát hiện lỗi thật |
| **2.6e** | `RestrictStaffMiddleware` (**Bẫy #6**), `ForceDefaultLanguageMiddleware` | Thứ tự middleware bắt buộc mà không gì bảo vệ | ✅ **Xong 2026-08-26** — 27 test, có cả khẳng định thứ tự |
| **2.6f** | `save_checkout_info` — tạo đơn, tạo `CartOrderItem`, luồng đơn treo | **Tiền đề bắt buộc của 2.11**: bước đó viết lại đúng hàm này | ✅ **Xong 2026-08-26** — 26 test, nhóm `CartOrderItemSnapshotTests` ghi rõ cái gì 2.11 được đổi |
| **2.6g** | `userauths` — đăng ký, đăng nhập, redirect theo vai trò | `userauths/tests.py` đang là stub rỗng | ✅ **Xong 2026-08-26** — 27 test |

**Ghi chú 2.6b (sau khi làm xong)** — lần dò đầu tiên ghi bốn hành vi sai: `safe_float`
trả `0.0` cho `'1.000.000,50'` (định dạng tiền Việt có phần thập phân, đúng thứ hàm này
tự nhận là xử lý) và cho `'1,234.56'`; `'-5'` ra `5.0` (mất dấu âm); `1e16` ra `116.0`.
Lúc đó đánh giá là **lỗi tiềm ẩn, không khai thác được**, vì sau bản vá
[S-02](SECURITY.md) giá vào session là `float` đọc từ database nên không đi qua nhánh
phân tích chuỗi.

**Đánh giá đó đúng một nửa.** Nhánh chuỗi thì đúng là không ai đi tới nữa, nhưng
`1e16 → 116.0` **không** thuộc nhánh đó: bản cũ ép mọi thứ qua `str()` trước, và
`str(1e16)` cho `'1e+16'`. Mà `Product.price` là `DecimalField(max_digits=20)`, tức giá
1e16 **nằm trong tầm hợp lệ của model**. Chiều ngược lại còn tệ hơn: `str(0.00001)` cho
`'1e-05'` → `105`, giá bị **thổi lên** chứ không phải giảm đi.

Nên bước này sửa hàm chứ không chỉ chốt hành vi. Ba quy tắc mới: số thì không đi qua
`str()`; dấu đứng sau là dấu thập phân (`1.000.000,50` và `1,234.56` chỉ khác thứ tự hai
dấu); đọc không được thì trả `default` chứ **không lọc bỏ ký tự lạ rồi tính trên phần còn
lại** — chính bước lọc đó biến `'[1]'` thành `1.0` và nuốt dấu trừ.

**Ghi chú 2.6f** — không phải unit test thuần (cần database), nhưng xếp ở đây vì cùng mục
đích: dựng lưới an toàn trước khi 2.11 đụng vào luồng rủi ro nhất.

## Giai đoạn 3 — Sửa hình và bảng trong báo cáo

Nội dung soạn sẵn: **[bao-cao/](bao-cao/)**

### 3A — Bắt buộc: code mới đã làm hình sai

- [ ] **3.1** **Hình 10** (Thêm vào giỏ) — vẽ lại. Hình chỉ có 4 lifeline (Template, URL
      Dispatcher, `add_to_cart`, Django Session), **không có Product Model và Database**.
      Sau bản vá [S-02](SECURITY.md), `add_to_cart` bắt buộc truy vấn database để lấy giá.
      Sửa thêm: hình ghi *"Cộng thêm số lượng mới"* nhưng code **ghi đè**; hình ghi POST
      nhưng code dùng GET
- [ ] **3.2** **Hình 11** (Cập nhật giỏ) — bỏ nhánh `[Số lượng mới = 0] Xóa sản phẩm`,
      thêm bước kiểm tồn kho
- [ ] **3.3** **Hình 28, 29** — bỏ trạng thái *Chờ duyệt* và `status="in_review"`
      ([ADR-0002](DECISIONS.md) đã áp lên production)
- [ ] **3.4** **Hình 24** (Tương tác Trợ lý AI) — hình đang vẽ 429 đến **từ Gemini API**;
      sau [S-03](SECURITY.md) còn 429 đến từ chính hệ thống do throttle

### 3B — Vẽ mới

- [ ] **3.5** Tách **Hình 15** và vẽ thêm sơ đồ cho `vnpay_return` và **`vnpay_ipn`**.
      Hiện **không có sơ đồ nào cho IPN** — mà đó mới là chỗ kiểm chữ ký, kiểm số tiền và
      chống xác nhận trùng. Điểm nhấn VNPay đang bị giấu mất trong một hình gộp

### 3C — Mô tả cơ sở dữ liệu

- [ ] **3.6** **Bảng 30** — `product_status` đang ghi *"Trạng thái xử lý"*, **giống hệt**
      mô tả ở Bảng 32 và Bảng 33 dù nghĩa hoàn toàn khác nhau (đăng bán vs giao hàng).
      Chính là bẫy #1, và báo cáo đang che mất nó
- [ ] **3.7** **ERD Hình 45** — `tags` không phải cột VARCHAR (django-taggit lưu ở bảng
      riêng); thiếu bảng nối M2M `cartorder ↔ coupon`; bỏ `core_tag` khỏi Bảng 28
- [ ] **3.8** Bổ sung khóa ngoại mới của 2.11 vào ERD và **Bảng 33**
- [ ] **3.21** **UC 3.2.25** (Hủy đơn) — bổ sung hai tiền điều kiện vào Pre-Conditions:
      chỉ hủy đơn còn `processing` và **chưa thanh toán** ([ADR-0007](DECISIONS.md)).
      Đây là chỗ code **hẹp hơn** báo cáo, ngược chiều với A2
- [ ] **3.22** **Bảng 32** — bổ sung giá trị `cancelled` vào mô tả `cartorder.product_status`
- [ ] **3.23** **ERD Hình 45** và bảng mô tả `core_coupon` — bổ sung `valid_to`,
      `used_count`, `usage_limit`. ⚠️ **Chưa tra được số hiệu "Bảng N" của `core_coupon`**
      trong repo, phải mở bản gốc PDF
- [ ] **3.24** **UC 3.2.21** — đối chiếu bản gốc xem "số lượt" là **bộ đếm** hay **hạn
      mức**. Code cài cả hai; nếu báo cáo chỉ mô tả bộ đếm thì `usage_limit` là thuộc
      tính mới cần bổ sung ([A6](SPEC-GAPS.md))
- [ ] **3.25** **UC 3.2.3** — đối chiếu Alternate Flow xem có ghi cỡ trang cụ thể không.
      Code dùng 8 sản phẩm/trang
- [ ] **3.26** **UC 3.2.21** (Áp mã giảm giá) — bổ sung tiền điều kiện *đơn chưa được
      chuyển sang cổng thanh toán* ([ADR-0008](DECISIONS.md)). Cùng loại bổ sung với hai
      tiền điều kiện của UC 3.2.25 ở bước 3.21 — lại là chỗ code **hẹp hơn** báo cáo
- [ ] **3.27** **ERD Hình 45** và bảng mô tả `cartorder` — bổ sung cột `vnpay_amount`
      (migration `0011`)

### 3D — Định vị và tác nhân ([ADR-0003](DECISIONS.md) đã chốt)

- [ ] **3.9** Mục 1.2.1 — "Người bán (Vendor/Nhân viên cửa hàng)" → **"Nhân viên cửa
      hàng"**; bỏ *"thuộc quyền sở hữu của gian hàng mình"* ([B1](SPEC-GAPS.md))
- [ ] **3.10** Mục 1.3 Phạm vi — "Người bán (Vendor/Staff)" → "Nhân viên cửa hàng"
- [ ] **3.11** Hình 4 và các use case của "Người bán"; **Bảng 41** danh sách giao diện
- [ ] **3.12** ADR-0001 — bổ sung generalization Quản trị viên ─▷ Nhân viên vào Hình 4
      **nếu** bước 0.4 xác nhận là còn thiếu

### 3E — Lỗi trình bày

- [ ] **3.13** **Hai chỗ trùng số mục**: thân bài có hai mục **3.5** (ERD tr.54 và
      UI/UX tr.67); **đề cương tr.3–4 có hai mục 3.3** (Lược đồ tuần tự và Lược đồ lớp)
- [ ] **3.14** tr.92 caption ghi *"Hình 3.5.23"*, và hình này **thiếu trong Danh mục hình
      ảnh** (nhảy từ Hình 71 sang Hình 72)
- [ ] **3.15** tr.6 câu định nghĩa vòng về Shopee
- [ ] **3.16** Tên Chương 2 lệch giữa đề cương và thân bài
- [ ] **3.17** tr.1 lời cảm ơn ký *"Nhóm sinh viên"* nhưng là đồ án cá nhân
- [ ] **3.18** Chương 2 bổ sung **DRF, i18n/gettext, WhiteNoise, django-taggit**
- [ ] **3.19** Chương 4 mục 4.1.2 bước 6 — bỏ `makemigrations` khỏi hướng dẫn cài đặt
      (migration đã commit; chạy thêm chỉ sinh migration rác), thêm cảnh báo `.env`
- [ ] **3.20** Đổi mật khẩu 3 tài khoản in ở tr.108 ([S-06](SECURITY.md))

## Giai đoạn 4 — Nội dung mới cho KLTN

Đây là phần trả lời câu hỏi chắc chắn sẽ bị hỏi: *"khác gì bản Tiểu luận?"*

- [ ] **4.1** Chương/mục **rà soát bảo mật** — **13 lỗ hổng** ở [SECURITY.md](SECURITY.md), 12 đã vá,
      kịch bản khai thác, cách vá, và cái gì **cố ý không vá** kèm lý do.
      Phần đáng giá nhất không phải danh sách lỗi mà là mục *Rà soát 2026-08-26*: **ba
      phát hiện ban đầu bị bác bỏ** khi có bước phản biện độc lập. Thấy `@csrf_exempt`
      trong code **chưa đủ để kết luận có lỗ hổng** — còn phải trả lời được request của
      kẻ tấn công có mang được cookie phiên tới không, mà điều đó phụ thuộc `SameSite`
- [ ] **4.2** Viết lại **Chương 4** — từ 5 test case thủ công lên **513 test tự động**
      (số tính tới 2026-08-26), cộng bảng test case cho AI Chatbot và VNPay.
      Điểm mạnh hơn con số: nay trình bày được thành **kim tự tháp test** — unit test
      thuần (`SimpleTestCase`, không DB) / test ở mức model / test hồi quy ở mức HTTP
- [ ] **4.3** Mục **quyết định kiến trúc** dựa trên 6 ADR, có cả phương án đã loại và lý
      do. Cặp ADR-0005 → ADR-0006 là ví dụ tốt: cùng dữ kiện kỹ thuật, hai kết luận khác
      nhau vì ràng buộc dự án khác nhau
- [ ] **4.4** Cập nhật **Kết luận** — mục *Nhược điểm* và *Hướng phát triển* phải phản
      ánh trạng thái mới, không bê nguyên từ bản Tiểu luận

---

## Đã xong

### 2026-08-26 — Bước 2.5, 2.14, 2.15: đóng nốt bảng lỗ hổng

**454 → 513 test**, năm commit. [SECURITY.md](SECURITY.md) nay **12/13 mục đã vá**; mục
còn lại là [S-06](SECURITY.md) — không phải lỗi code mà là ba mật khẩu in trong báo cáo,
đổi sau khi bảo vệ.

Lô này sinh ra [ADR-0008](DECISIONS.md) và **hai migration** (`0010`, `0011`), và lần đầu
tiên trong dự án việc deploy có **điều kiện bắt buộc** — xem khối 🚨 ở [giai đoạn 1](#giai-đoạn-1--deploy).

- **S-05 + S-11** — thiếu `DJANGO_SECRET_KEY` khi `DEBUG=False` nay là `ImproperlyConfigured`
  lúc khởi động, `DJANGO_DEBUG` đảo mặc định thành `'0'`, hai cờ `Secure` của cookie thành
  nghịch đảo của `DEBUG`. Khóa dự phòng thay bằng khóa mới: khóa cũ còn nằm trong lịch sử
  git của một repo public nên không được tiếp tục làm giá trị dự phòng ở đâu cả.

  **Lượt đột biến đầu tiên bắt được một lỗ hổng trong chính cách test.** Khôi phục đúng
  mặc định cũ (`_env_flag('DJANGO_DEBUG', '1')`) mà **không test nào đỏ**, vì mọi test đều
  tự truyền giá trị mặc định vào lời gọi của chính nó — tức chúng kiểm *hàm*, không kiểm
  *chỗ gọi*. Phải thêm `DJANGO_SKIP_DOTENV` để nạp lại được cả module với môi trường giả
  thì mới phủ được chỗ gọi. Đây là biến thể mới của bài học ở bước 2.8/2.9, lần này ở tầng
  cấu hình chứ không phải tầng nghiệp vụ.

- **S-07** — bỏ hẳn khối `try`/`except:` trần ở luồng đăng nhập. Nó không cần thiết ngay
  từ đầu: `User.objects.get()` chỉ tồn tại để sinh ra `DoesNotExist`, mà `authenticate()`
  đã trả `None` cho cả hai trường hợp sai.

  Lộ ra thêm một thứ không nằm trong mô tả của S-07: hai nhánh sai trả **hai thông điệp
  khác nhau** — "User does not exist" cho sai mật khẩu, "User with email X does not exist"
  cho email chưa đăng ký. Đó là **oracle liệt kê tài khoản**, và vế sau còn dội thẳng
  chuỗi người dùng gửi lên ra template. Nay gộp làm một.

- **S-10** — năm endpoint đổi dữ liệu của người khác chuyển sang POST + CSRF. Phần tốn
  công không phải view mà là **template**: ba lời gọi AJAX, năm link đăng xuất và nút
  VNPay đều phải thành form.

  Đó cũng là chỗ loại thay đổi này hay hỏng: view vá xong, nút vẫn hiện, bấm vào trả
  **405**, và không test nào ở tầng view thấy. Nên có hẳn hai nhóm test khẳng định
  **markup** là form POST chứ không phải `<a href>` — cám dỗ "sửa cho đẹp" bằng cách trả
  về link là có thật, nút form khó style hơn link.

  Bốn endpoint giỏ hàng **cố ý giữ GET**: chúng chỉ đụng session của chính người gửi nên
  không có dữ liệu của ai khác để giả mạo. Có một nhóm test nói rõ điều đó, để lần sau ai
  đọc S-10 rồi thấy chúng còn GET thì biết là đã cân nhắc chứ không phải bỏ sót.

- **S-12** — `Coupon.discount` vá ở **ba** mức chứ không một: validator 1–100 chặn đường
  nhập liệu (chỉ chạy qua ModelForm, tức Django admin), `CHECK (discount >= 0)` từ
  `PositiveIntegerField` chặn ở tầng database, và kẹp trong `checkout()` lo cận trên cùng
  các bản ghi có từ trước.

  Viết test làm đổi một kết luận: test cho "bản ghi âm có sẵn" được viết để chứng minh
  cái kẹp xử lý được nó, và nó **lỗi** thay vì đỏ — `CHECK` mới từ chối bản ghi ngay từ
  đầu. Khẳng định đúng là `IntegrityError`, mạnh hơn hẳn điều định chứng minh ban đầu.

- **S-13** — chỗ nghiêm trọng nhất của lô, dù xếp mức Trung bình: `vnpay_ipn` đối chiếu
  callback với `order.price` **lúc nhận** thay vì số tiền **đã gửi**, nên khách trả tiền
  thật mà đơn không bao giờ được ghi nhận. Chi tiết và các phương án đã loại ở
  [ADR-0008](DECISIONS.md).

  Nhánh dự phòng cho `vnpay_amount IS NULL` là **bắt buộc**, không phải cho gọn: bỏ đi là
  mọi đơn treo trên production hỏng ngay khi deploy. Có test riêng cho đúng điều đó, và
  nó đỏ khi thử bỏ nhánh.

**Kiểm chứng.** Mười tám đột biến, mỗi bản vá 3–6 cái, **tất cả đều làm đỏ ít nhất một
test**. Nhưng như mục S-05 ở trên cho thấy, điều đáng ghi cho [bước 4.1](#giai-đoạn-4--nội-dung-mới-cho-kltn)
không phải con số đó — mà là lượt đột biến **thất bại** ở lần đầu, và những gì nó buộc
phải sửa trong chính bộ test.

**Ba lần giả định sai bị test bắt**, cả ba đều là giả định của người viết chứ không phải
lỗi code: `payment_method` mặc định đã là `'online'` và `product_status` mặc định đã là
`'processing'` nên không field nào của `vnpay_payment` quan sát được (phải dựng đơn ở
`shipped`); và bản ghi coupon âm không tồn tại được nữa sau migration `0010`.

**Còn nợ lại:** thông điệp trong `userauths/views.py` **chưa qua i18n** — hiện tiếng Anh
ở cả hai ngôn ngữ. Có từ trước lô này; bọc một chuỗi trong khi hàng xóm của nó không bọc
thì tệ hơn là để nguyên cho nhất quán. Cần một lượt riêng cho cả file.

### 2026-08-26 — Bước 2.6b, 2.6c, 2.6e, 2.6g: đóng nốt tầng unit test

**346 → 454 test.** Nhóm 2.6 khép lại. Ba file mới, và **một hàm trên đường tiền được
sửa** — phần còn lại chỉ chốt hành vi sẵn có.

Không đụng model nên **không có migration**, và không đụng chức năng nào báo cáo mô tả
nên **không phải sửa một chữ nào trong báo cáo** — trừ con số ở [bước 4.2](#giai-đoạn-4--nội-dung-mới-cho-kltn).

- **2.6b — `safe_float` phải sửa, không chỉ chốt.** Chi tiết ở *Ghi chú 2.6b* phía trên.
  Tóm tắt chỗ đáng nhớ: bản cũ ép **mọi** đầu vào qua `str()` rồi lọc bỏ ký tự lạ và tính
  trên phần còn lại. Cách đó biến `'[1]'` thành `1.0`, nuốt dấu trừ, và — nguy hiểm nhất —
  đọc `str(1e16) == '1e+16'` thành **116**. Giá 1e16 nằm trong tầm hợp lệ của
  `DecimalField(max_digits=20)`, nên đây không phải trường hợp giả định.

  Viết test trước: **10/54 đỏ** đúng bốn nhóm hành vi sai, 44 test còn lại chốt những chỗ
  bản cũ vốn đã đúng để bản mới không làm lệch. Sau khi sửa, toàn bộ 454 test xanh —
  tức không chỗ nào trong luồng checkout phụ thuộc vào hành vi cũ.

- **2.6c — `vnd` / `mul` không phải sửa gì.** Hai filter này viết bằng `Decimal` và
  `ROUND_HALF_UP` ngay từ đầu, đúng cả ở chỗ dễ sai nhất: `mul('0.1', 3)` ra `0.3` chứ
  không phải `0.30000000000000004`.

- **2.6e — và một test trang trí bị bắt tại chỗ.** Bản đầu của nhóm tích hợp dùng
  `core:index` để chứng minh `RestrictStaffMiddleware` đã được lắp vào settings. Gỡ hẳn
  middleware khỏi `MIDDLEWARE` thì test đó **vẫn xanh**: `index()` có sẵn nhánh chuyển
  hướng nhân viên **trùng lặp** với middleware, nên trang chủ là chỗ duy nhất không dùng
  để kiểm chứng middleware được. Đã đổi sang `core:product-list`, và giữ lại một test ghi
  rõ sự trùng lặp đó để lần sau không ai mất công dò lại.

  Nhóm này còn khẳng định **thứ tự** trong `settings.MIDDLEWARE` — thứ mà không test đơn
  lẻ nào thấy được, vì mỗi lớp vẫn đúng chức năng của nó, chỉ là chạy sai lúc.

- **2.6g — và một giả định sai của chính tôi.** Test đầu tiên viết ra khẳng định đăng ký
  **chấp nhận** trùng `username`, vì model khai đè `username` thành `CharField` thường
  (bỏ `unique=True` của `AbstractUser`). Test đỏ: `UserCreationForm` của Django mang sẵn
  `clean_username` từ chối tên đã tồn tại, không phân biệt hoa thường.

  Kết luận đúng là **form chặt hơn database**, nên nay có hai test cho hai mức: form từ
  chối, còn `User.objects.create_user` / Django Admin / shell thì vẫn tạo được hai người
  trùng tên. Nghĩa là **đừng viết code nào coi `username` là khóa**.

**Kiểm chứng.** Tám đột biến được áp lần lượt rồi gỡ ra — gỡ `RestrictStaffMiddleware`
khỏi settings, đảo thứ tự hai middleware ngôn ngữ, bỏ tiền tố sign-out, bỏ lệnh xóa
`Accept-Language`, bỏ rẽ nhánh theo vai trò khi đăng nhập, bỏ tự-đăng-nhập sau đăng ký,
gỡ signal tạo `Profile`, bỏ `logout()`. **Cả tám đều làm đỏ ít nhất một test**, và chính
lượt này đã lộ ra test trang trí ở 2.6e.

Nhắc lại bài học của [bước 4.1](#giai-đoạn-4--nội-dung-mới-cho-kltn): tự gỡ chốt ra thử
là **điều kiện cần, không phải điều kiện đủ** — nhưng ở đây nó đúng là thứ bắt được lỗi.

### 2026-08-26 — Bước 2.8 + 2.9: phân trang và mã giảm giá

**258 → 346 test**, tám commit. Đóng nốt [A3](SPEC-GAPS.md) và [A6](SPEC-GAPS.md), nên
**nhóm A chỉ còn A10** (email hàng loạt) và **A11** (cố ý không cài).

Lô này bắt đầu bằng một lượt phân tích song song năm góc nhìn trên repo trước khi viết
dòng code nào. Nó tìm ra **hai lỗi có sẵn** mà kế hoạch ban đầu không biết, và cả hai đều
phải sửa trước thì phân trang mới đúng được.

**Lỗi có sẵn #1 — thiếu `order_by` ở 9 truy vấn danh sách.** Không model nào khai
`Meta.ordering`. Phân trang một queryset không có `ORDER BY` thì PostgreSQL được tự do
trả bản ghi theo thứ tự bất kỳ, nên cùng một sản phẩm có thể hiện ở cả trang 1 lẫn trang
2, hoặc không hiện ở trang nào.

Điểm đáng ghi cho [bước 4.1](#giai-đoạn-4--nội-dung-mới-cho-kltn): **lỗi này không tái
hiện được ở máy local.** SQLite gần như luôn trả bản ghi theo `rowid` nên nhìn y hệt đã
sắp đúng; nó chỉ xuất hiện sau khi deploy lên Neon. Vì vậy `core/test_ordering.py` khẳng
định **cấu trúc truy vấn** (`qs.ordered`, `qs.query.order_by`) chứ không khẳng định "mở
trang 2 thấy có dữ liệu" — kiểu sau vẫn xanh trên SQLite kể cả khi gỡ hết `order_by`.

**Lỗi có sẵn #2 — bộ lọc nuốt mất mục "Khuyến mãi trong ngày".**
`<div id="filtered-product-grid">` **không được đóng**. Trình duyệt tự vá nên nhìn bằng
mắt không thấy gì, nhưng jQuery thì tính đúng biên thật của phần tử: vùng bị
`$(...).html()` ghi đè kéo dài từ dòng 167 tới 232, ôm trọn mục Deals ở dòng 191. Tick
một checkbox là mục đó biến mất.

Loại lỗi này **test HTTP thông thường không thấy** — HTML server trả về vẫn đủ mọi thứ.
`core/test_product_list_layout.py` phải tự đếm cân bằng thẻ `<div>` để suy ra biên thật
của vùng ghi đè rồi mới khẳng định được mục Deals nằm ngoài.

- **2.8** — 8 sản phẩm/trang ở 5 trang phía khách. Danh sách **danh mục** và **thương
  hiệu** cố ý không phân trang; thay vào đó **gỡ thanh phân trang giả** mà theme để lại:
  ba template đang render một thanh tĩnh 6 số trang với link `href="#"` trỏ vào hư không.
  Đó là giao diện nói dối khách hàng thật, và người chấm bấm vào là thấy.

  Chỗ khó nhất là bộ lọc AJAX. Thanh phân trang phải nằm **ngoài** vùng bị ghi đè nên
  `filter_product` trả nó về dưới một khóa JSON riêng, và trả `paginator.count` chứ không
  phải độ dài trang — con số đó đi thẳng vào dòng "We found N items". Khi đã lọc thì cú
  bấm phân trang quay lại đường AJAX, vì `product_list_view` không đọc tham số lọc; chưa
  lọc thì link server render là link thật, chạy cả khi tắt JS.

- **2.9** — `valid_to`, `usage_limit`, `used_count`. Bộ đếm tăng ở
  `CartOrder.confirm_paid()`, nay là **chỗ duy nhất** được phép ghi `paid_status=True`.

  Gom về một chỗ vá luôn một lỗ có sẵn: `vnpay_ipn` có chốt `if order.paid_status` còn
  `vnpay_return` thì **không**, mà VNPay hoàn toàn có thể gọi cả hai cho một đơn.

  Tăng bộ đếm lúc **trả tiền** chứ không lúc **áp mã** — bốn đường làm con số sai nếu
  tăng lúc áp: đơn treo không bao giờ thanh toán; `save_checkout_info` gọi
  `coupons.clear()` mỗi lần khách sửa giỏ nên áp lại là +1 cho cùng một đơn; hủy đơn chỉ
  ghi `product_status`; và trang thanh toán thất bại in sẵn link quay lại checkout.

- **Sót của 2.10 đã vá.** `place_cod_order` và `vnpay_payment` đều từ chối đơn đã hủy,
  nhưng `checkout()` — **chính là trang áp mã** — thì không. Và đơn COD đã đặt vẫn có
  `paid_status=False` cho tới lúc giao, nên chốt `paid_status` sẵn có cũng không chặn:
  khách đặt COD xong quay lại URL cũ là hạ giá được một đơn đang giao.

**Hai lỗ hổng mới ghi nhận, cố ý không vá:** [S-12](SECURITY.md) (`Coupon.discount` không
có validator → giá đơn âm → gửi số tiền âm sang VNPay) và [S-13](SECURITY.md) (`vnpay_ipn`
so số tiền theo giá **hiện tại** nên áp mã sau khi đã chuyển sang cổng là đơn không bao
giờ được ghi nhận đã trả). Cả hai đều là lỗi thật nhưng không neo vào UC nào của 2.8/2.9;
vá kèm là commit mất khả năng truy nguyên.

**Kiểm chứng, và giới hạn của nó.** Mọi chốt chặn mới đều được thử gỡ ra để xác nhận có
test bắt được. Nhưng cách làm đó chỉ soi được **những chỗ mình nghĩ tới**, nên sau khi
xong còn chạy thêm một lượt **review đối kháng** trên toàn bộ diff — bốn góc nhìn song
song, mỗi phát hiện bị một agent khác cố bác bỏ trước khi được tính. Nó tìm ra **12 vấn
đề thật**, trong đó có ba thứ đáng ghi lại:

1. **Một hồi quy do chính bước 2.8 gây ra.** Bốn template in `{{ products.count }}`, mà
   `products` nay là `Page`. `Page` kế thừa `Sequence`, `Sequence.count(value)` bắt buộc
   một tham số, nên template engine dính `TypeError` rồi thay bằng `string_if_invalid` —
   **chuỗi rỗng**. Không 500, không log, chỉ mất con số. Trang hiện ra
   `We found <strong></strong> item for you!` suốt mà 328 test vẫn xanh.

2. **Một lỗ hổng kiểm thử ngay giữa điểm nhấn của đề tài.** `confirm_paid()` sinh ra để
   xử lý việc `vnpay_return` và `vnpay_ipn` có thể cùng chạy cho một đơn — nhưng **không
   test nào từng gọi hai endpoint đó**. Đo được: gỡ cả hai lời gọi `confirm_paid()` về
   như trước bước 2.9 thì **toàn bộ suite vẫn xanh**. Mọi bảo đảm của 2.9 hóa ra chỉ được
   bảo vệ ở nhánh COD. Nay có `core/test_vnpay_flow.py`, và cùng phép thử đó làm đỏ 5 test.

3. **Bốn test do chính lượt này viết ra là test trang trí.** Ví dụ rõ nhất:
   `test_the_price_slider_still_sees_every_price` tạo sản phẩm đắt nhất **sau cùng** nên
   nó rơi đúng vào trang 1 — mà ở đó `aggregate()` chạy nhầm trên `Page` cũng cho ra đúng
   kết quả. Docstring của test nói nó bắt lỗi ấy; thực tế thì không.

Bài học cho [bước 4.1](#giai-đoạn-4--nội-dung-mới-cho-kltn): **tự gỡ chốt chặn ra thử là
điều kiện cần, không phải điều kiện đủ.** Nó không phát hiện được thứ mình chưa nghĩ tới
là phải kiểm — và ba mục trên đều thuộc loại đó.

**Giới hạn đã biết của 2.8:** URL không phản ánh trạng thái bộ lọc → F5 mất bộ lọc, không
share được link đã lọc. Ghi thành **bước 2.8b**.

**Đánh đổi đã biết của 2.9:** kiểm "còn lượt không" ở lúc áp mã, tăng bộ đếm ở lúc trả
tiền — hai thời điểm cách nhau tùy ý nên nhiều khách áp cùng lúc vẫn vượt được hạn mức.
Chấp nhận và giải thích trong phần *hạn chế* của báo cáo: không có luồng hoàn tiền
([ADR-0007](DECISIONS.md)) nên bộ đếm chỉ đi một chiều. `select_for_update()` cũng **không
có tác dụng trên SQLite**, nên test chứng minh được tính idempotent chứ không chứng minh
được chống tranh chấp — docstring của test ghi rõ điều đó.

### 2026-08-26 — Bước 2.10 + 2.7: vòng đời đơn hàng

**207 → 258 test.** Hai bước làm chung một lô vì cùng đụng trang chi tiết đơn ở cả hai
phía, và vì 2.7 phải biết `cancelled` tồn tại (đơn đã hủy thì không có lô hàng để theo
dõi). Đóng thêm **hai** mục nhóm A: [A7](SPEC-GAPS.md) và [A9](SPEC-GAPS.md).

- **2.10** — trạng thái `cancelled`, khách tự hủy ở trang đơn hàng, nhân viên hủy được từ
  dashboard. Điều kiện hủy và lý do chọn chúng nằm ở **[ADR-0007](DECISIONS.md)**; tóm
  tắt: chỉ hủy đơn còn `processing` và **chưa thanh toán**.

  Cả hai điều kiện được chọn không phải vì đúng nghiệp vụ hơn mà vì chúng **xóa bỏ một
  lớp lỗi**: không cho hủy sau `shipped` nghĩa là không tồn tại nhánh hoàn kho nào để
  viết sai; không cho hủy đơn đã trả tiền nghĩa là không sinh ra đơn vừa hủy vừa đã thu
  tiền mà không màn hình nào xử lý được.

- **Ba đường hồi sinh đơn đã hủy, cả ba đều phải chặn.** `place_cod_order` và
  `vnpay_payment` đều gán thẳng `product_status = 'processing'` không kiểm gì.
  `_get_pending_order_from_session` thì tái sử dụng đơn treo cho lần thanh toán sau.

  Chốt thứ ba suýt lọt lưới: test đầu tiên tôi viết cho nó **vẫn xanh khi gỡ chốt**, vì
  nó đi đường khách-tự-hủy mà đường đó đã dọn `pending_order_oid` khỏi session từ trước.
  Kịch bản thật là **nhân viên** hủy — khách không đụng gì vào session của mình. Đã viết
  lại test cho đúng đường đó. Ghi lại vì đây là kiểu test tự-thỏa-mãn khó thấy: nó chạy
  qua đúng chức năng, chỉ là không chạy qua đúng nhánh.

- **`cancelled` vào `STATUS_CHOICES` là tự động hiện trong dropdown của nhân viên** (danh
  sách dựng từ model). Đó là điều mong muốn, nhưng kéo theo một hệ quả: whitelist *giá
  trị hợp lệ* **không đủ**, vì `cancelled` là giá trị hợp lệ mà không phải bước chuyển
  hợp lệ từ mọi trạng thái. Phải thêm chốt riêng cho bước chuyển `→ cancelled`.

- **2.7** — ô nhập mã vận đơn ở trang nhân viên, và mã hiện luôn ở trang đơn hàng của
  khách. Không đụng cơ sở dữ liệu: `tracking_id` đã có trong model từ migration đầu tiên,
  chỉ chưa bao giờ có giao diện (muốn sửa phải vào Django Admin). Đây là mục hiếm trong
  nhóm A mà báo cáo mô tả **đúng** còn code thiếu.

  Form **riêng**, không gộp vào form đổi trạng thái: hai thao tác độc lập, gộp lại thì
  sửa mã vận đơn là đơn nhảy trạng thái theo. Chuỗi rỗng lưu thành `NULL` chứ không phải
  `''`, để trang của khách chỉ phải kiểm một trường hợp "chưa có mã" thay vì hai.

**Kiểm chứng:** bốn chốt chặn mới đều được thử gỡ ra để xác nhận có test bắt được —
không cái nào là test trang trí.

**Còn nợ lại:** nhãn trạng thái đơn (`Processing`/`Shipped`/`Delivered`/`Cancelled`) lấy
thẳng từ `choices` của model nên **chưa qua i18n**, hiện tiếng Anh ở cả hai giao diện.
Đây là tình trạng có sẵn từ trước chứ không phải do bước này sinh ra, nhưng nay nó lộ rõ
hơn vì trạng thái được hiển thị ở thêm một trang nữa.

### 2026-08-26 — Bước 2.11 + 2.12: khóa ngoại `CartOrderItem` → `Product`

**174 → 207 test.** Đây là hạng mục đầu tiên của KLTN đóng một gap **nhóm A** mà báo cáo
đã đặc tả sẵn cả use case lẫn lược đồ tuần tự — **không phải sửa một chữ nào trong báo
cáo**, chỉ phải bổ sung khóa ngoại vào ERD (bước 3.8, vốn đã nằm trong kế hoạch).

- **2.11** — `CartOrderItem.product`, `on_delete=SET_NULL`, chạy **song song** với bản sao
  tĩnh chứ không thay nó. Snapshot vẫn giữ hóa đơn không đổi khi sản phẩm bị sửa hay xóa;
  khóa ngoại trả lời câu *"dòng này vốn là sản phẩm nào"*. Ba test
  `test_the_snapshot_survives_*` viết từ bước 2.6f **xanh nguyên**, đúng như nhóm đó dự
  liệu — bằng chứng là hai cơ chế không giẫm chân nhau. Đúng **một** test phải đổi kỳ
  vọng (`test_there_is_no_link_back_to_the_product`), và đó chính là test mà 2.6f đã ghi
  sẵn là sẽ phải đổi.

  Đường tra ngược **thẳng hơn ghi chú kế hoạch cũ**: khóa của `cart_data_obj` chính là
  khóa chính của sản phẩm (`add_to_cart` ép `id` phải là chữ số), nên không cần đi vòng
  qua `pid`. `save_checkout_info` tra một truy vấn cho cả giỏ, dùng `all_objects` để sản
  phẩm bị ngừng bán lúc còn nằm trong giỏ vẫn nối được.

- **Nợ kỹ thuật #6 đã vá.** `change_order_status` trước đây trừ kho bằng
  `Product.objects.filter(title=item.item).first()`. Ba test mới chốt lại lỗi đó, và
  **cả ba đều đỏ khi thử khôi phục code cũ** — không phải test trang trí:
  trùng tên thì `.first()` trừ kho của sản phẩm *không được mua*; đổi tên sau khi bán thì
  không trừ được gì.

- **Chỗ cố ý KHÔNG dùng khóa ngoại.** `product_has_order_history` vẫn so tên, nhưng chỉ
  cho dòng `product IS NULL`. Lý do là hai chiều sai ở đó không nguy hiểm ngang nhau:
  nhầm CÓ → xóa mềm (khôi phục được), nhầm KHÔNG → **xóa cứng** (mất hẳn). Ở
  `change_order_status` và `has_purchased` thì ngược lại, nên hai chỗ đó không có lưới
  hứng theo tên. **Cùng một dữ liệu thiếu, ba cách xử lý khác nhau tùy hướng của rủi ro**
  — đáng đưa vào [bước 4.1](#giai-đoạn-4--nội-dung-mới-cho-kltn).

- **Migration `0007` có backfill, và backfill đó được test.**
  [core/test_migration_0007.py](../grocerly/core/test_migration_0007.py) chạy migration
  thật bằng `MigrationExecutor` chứ không gọi hàm với model hiện tại — vì model lịch sử ở
  trạng thái `0006` **chưa có** cột `product`, đúng điều kiện cần tái hiện. Backfill **cố
  tình không đoán bừa**: tên ứng với hai sản phẩm thì để `NULL`. Ba test kỳ vọng nối được
  đều đỏ khi thử vô hiệu hóa backfill.

- **2.12** — `has_purchased`, kiểm ở **server** (`403`) chứ không chỉ ẩn form; S-08 đã cho
  thấy chốt chặn nằm mỗi ở template thì POST thẳng vào endpoint là đi qua được. Trang chi
  tiết ẩn form **kèm câu giải thích** — ẩn không nói lý do thì khách tưởng chức năng hỏng.

  Nhận cả `shipped` lẫn `delivered` dù UC 3.2.14 chỉ viết *Shipped*: `delivered` nằm sau
  `shipped` nên hiểu theo nghĩa hẹp là khách nhận hàng xong lại **mất** quyền đánh giá.
  Ghi lại trong [SPEC-GAPS](SPEC-GAPS.md) như một chỗ code rộng hơn báo cáo **có chủ ý**.

- **Cặp ADR-0005 → ADR-0006 nay có kết cục.** ADR-0005 loại A2 với lý do: chỉ so được
  theo tên nên đổi tên sản phẩm là chặn nhầm người mua thật. Nhóm `RenameAndDeleteTests`
  chốt lại rằng lý do đó đã hết hiệu lực — đúng thứ [bước 4.3](#giai-đoạn-4--nội-dung-mới-cho-kltn)
  cần: một quyết định bị đảo ngược, và bằng chứng bằng test rằng việc đảo là đúng.

**Còn nợ lại (không thuộc phạm vi 2.11/2.12):** form thêm đánh giá ở
`templates/core/product-detail.html` submit bằng **POST thường** tới một endpoint trả
JSON — không có handler AJAX nào, dù `<strong id="review-res">` cho thấy đã từng định
làm. Khách bấm Gửi sẽ thấy JSON thô. Lỗi này có từ trước, và sửa/xóa đánh giá thì lại có
AJAX đầy đủ. Chưa sửa vì nằm ngoài phạm vi hai bước này.

### 2026-08-26 — Bước 2.1, 2.2, 2.3, 2.4, 2.6a, 2.6d + rà soát endpoint

**49 → 174 test.** Tám commit, `038701f`…`dbf8c3d` cộng bước 2.6f.

- **2.3** — `clear_cart`, POST + CSRF, nút ở trang giỏ hàng. **Đừng nhầm với xóa từng
  sản phẩm**: `delete_item_from_cart` vốn đã có và vẫn chạy đúng; cái thiếu là xóa **sạch
  toàn bộ** trong một lần. Cơ chế xóa sạch đã tồn tại sẵn ở ba chỗ trong `core/views.py`
  nhưng cả ba đều chạy **sau khi thanh toán xong** nên khách không gọi tới được.

  Lộ ra một lỗi cũ: hai lời gọi `render_to_string` cho bản async của giỏ hàng **không
  truyền `request=`** (khác hai lời gọi tương tự cho product-list và wishlist trong cùng
  file), nên `{% csrf_token %}` render ra **rỗng**. Không ai trúng vì trước đó bản async
  chưa có form nào. Đã truyền thẳng token thay vì `request=request`, để không kéo theo
  context processor truy vấn Address/Wishlist mỗi lần đổi số lượng (nợ kỹ thuật #2).

  Nút phải đặt ở **cả hai** file — `cart.html` và `core/async/cart-list.html` gần như là
  bản sao của nhau (96 dòng mỗi file); thiếu ở bản async thì nút biến mất ngay sau khi
  khách xóa một sản phẩm.

  `clear_cart` cũng bỏ luôn `session['pending_order_oid']`, nếu không khách xóa sạch giỏ
  rồi bấm Thanh toán sẽ bị đá vào đúng cái đơn chứa những món vừa xóa. Bản ghi `CartOrder`
  chưa thanh toán **vẫn nằm nguyên** — xóa giỏ không phải hủy đơn ([A7](SPEC-GAPS.md),
  bước 2.10).

- **2.4** — migration `0006_drop_stripe_payment_intent`. Không phải quyết định mới: field
  đã rời `models.py` từ commit `0925f27` mà **chưa bao giờ có migration**, nên model và
  database lệch nhau suốt từ đó. Làm trước vì Django gom mọi thay đổi của một app vào
  **một file migration mỗi lần chạy** — để lâu là nó bám vào migration của 2.9/2.10/2.11
- **2.6a** — 18 unit test cho `core/vnpay.py` (`SimpleTestCase`, không dựng database;
  chữ ký kỳ vọng tính lại độc lập bằng `hmac`/`hashlib`). Lộ ra hai vấn đề: so chữ ký
  **phân biệt hoa thường** (rủi ro của lúc chuyển sang cổng thật — cổng sandbox hiện tại
  trả chữ thường nên chưa hỏng), và `validate_response` **sửa dữ liệu đầu vào của chính
  nó** nên gọi lần hai luôn trả `False`. Đã vá cả hai
- **2.6d** — 14 test cho hạ tầng xóa mềm, chốt **Bẫy #3** thành test. Phát hiện **lỗi
  thật**: `Vendor.restore()` chưa bao giờ khôi phục được sản phẩm, vì `soft_delete()` gọi
  `timezone.now()` **hai lần** (đo được lệch 563µs) rồi `restore()` lại khớp theo
  `deleted_at`. Vendor sống lại một mình với gian hàng trống. Docstring của
  `SoftDeleteModel` cũng mô tả một API không tồn tại (`all_objects.dead()` ném
  `AttributeError`)
- **2.1** — `delete_product` xóa mềm khi sản phẩm đã có đơn. Kèm: nút Delete từ
  `<a href>` (GET, không xác nhận) thành form POST + CSRF + hộp thoại xác nhận
- **2.2** — đơn `delivered` là trạng thái cuối. Lộ ra **lỗi live**: option đầu của
  dropdown — cái được chọn sẵn — gửi `value="pending"`, giá trị **không có trong
  `STATUS_CHOICES`**, mà view gán thẳng không kiểm. Bấm Save khi chưa chọn gì là đơn rơi
  vào trạng thái không tồn tại. Nay option dựng từ model, view lọc qua whitelist, và bỏ
  `@csrf_exempt` (template vốn đã gửi token)
- **[S-09](SECURITY.md)** — `ajax_contact_form` ghi database bằng GET không xác thực
- **2.6f** — 26 test cho `save_checkout_info`. Nhóm `CartOrderItemSnapshotTests` ghi rõ
  cái gì 2.11 **phải giữ nguyên** (bản sao tĩnh của hóa đơn) và cái gì **phải đổi**
  (`test_there_is_no_link_back_to_the_product`), để 2.11 làm lệch là thấy ngay
- **Lỗi sập trang chủ** — phát hiện tình cờ khi viết test cho 2.6f. `Product.category` và
  `Product.vendor` đều `null=True`, `AddProductForm` để cả hai `required=False`, mà 11 chỗ
  trong template gọi thẳng `{% url ... p.category.c_id %}`. Khi None, template cho ra
  **chuỗi rỗng** rồi `{% url %}` ném `NoReverseMatch` → **trang chủ 500 cho mọi khách**.
  Nhân viên chỉ cần thêm sản phẩm mà quên chọn danh mục là sập. `add_product` có giá trị
  dự phòng cho `vendor` nhưng **không có** cho `category`

**Rà soát endpoint đổi trạng thái** (46 phát hiện thô → 29 qua phản biện → 13 sau khi gộp)
— kết quả ở [SECURITY.md](SECURITY.md) mục S-09 đến S-11. Đáng ghi lại cho
[bước 4.1](#giai-đoạn-4--nội-dung-mới-cho-kltn): **ba phát hiện ban đầu là sai** và chỉ
lộ ra khi có bước phản biện độc lập.

### 2026-08-25 — Throttle chatbot, filter trạng thái, sửa/xóa đánh giá

- **[S-03](SECURITY.md)** — throttle `/api/v1/chat/` theo IP và theo tài khoản, giới hạn
  độ dài `message` và số lượt `history`. Bắt được thêm một lỗi: response 429 mặc định của
  DRF là `{"detail": ...}` mà widget chat chỉ đọc `reply`/`error` nên bị nuốt im lặng
- **Backlog I** — filter "Status" ở trang sản phẩm trước đây là UI chết (`<select>` không
  có `name`, không nằm trong form) và ba lựa chọn *Active/Disabled/Show all* còn không
  khớp giá trị model
- **[A1](SPEC-GAPS.md)** — `ajax_edit_review` và `ajax_delete_review`, đặt đúng tên báo
  cáo ghi ở Hình 22–23

### 2026-08-24 — ADR-0002: bỏ luồng duyệt sản phẩm

`STATUS` rút còn `draft`/`published`/`disabled`, mặc định `draft`. Migration
`0005_product_status_drop_review_flow` **đã áp lên production Neon** — xác minh trước là
no-op (7 sản phẩm đều `published`, `sqlmigrate` báo `AlterField` không sinh DDL).

Nhân viên tự quyết trạng thái bằng nút bấm qua whitelist `PRODUCT_STATUS_ACTIONS`. Kèm
**[S-04](SECURITY.md)**: điều kiện hiển thị gom về `Product.objects.published()` thay cho
12 lần lặp `filter(product_status='published')` — chính sự lặp lại đó là lý do
`store_api` bị bỏ sót ngay từ đầu.

### 2026-08-24 — Vá ba lỗ hổng nghiệp vụ

**[S-01](SECURITY.md)** (bỏ qua thanh toán bằng URL), **[S-02](SECURITY.md)** (giả mạo
giá qua query string), **[S-08](SECURITY.md)** (chốt chặn đánh giá chỉ nằm ở template —
phát hiện thêm trong lúc rà), kèm **[A5](SPEC-GAPS.md)** (chặn vượt tồn kho).

Phát sinh: JS giỏ hàng **không có `error:` callback nào**, nên mọi mã 400/404 mới đều bị
nuốt im lặng. Đã thêm cho cả ba chỗ gọi.

### Hạ tầng kiểm thử

- [core/tests.py](../grocerly/core/tests.py), [useradmin/tests.py](../grocerly/useradmin/tests.py),
  [store_api/tests.py](../grocerly/store_api/tests.py) — **49 test**, tái hiện đúng kịch
  bản khai thác. Đây là test tự động đầu tiên của dự án
- [settings_test.py](../grocerly/grocerly/settings_test.py) — ép SQLite in-memory
- [settings_local.py](../grocerly/grocerly/settings_local.py) — ép SQLite trên đĩa, tắt
  Cloudinary, để `runserver` không đọc-ghi thẳng vào production

```bash
cd grocerly
python manage.py test --settings=grocerly.settings_test
```

---

## Không làm (đã cân nhắc và loại)

| Việc | Lý do loại |
|---|---|
| Cài đầy đủ luồng duyệt sản phẩm | [ADR-0002](DECISIONS.md) — sai mô hình nghiệp vụ. **Vẫn giữ quyết định này ở KLTN**: lý do là nghiệp vụ, không phải thiếu thời gian |
| Chuyển quyền tạo sản phẩm lên Admin | Đúng ngành hơn nhưng kéo theo sửa quá nhiều use case |
| Refactor `useradmin` để scope theo vendor | Không cần nữa sau khi chốt [ADR-0003](DECISIONS.md) |
| Chuyển giỏ hàng từ session sang model | Session hoạt động tốt và cho phép khách vãng lai mua hàng |
| Commit thư mục `.claude/` vào repo | [ADR-0004](DECISIONS.md) |
| ~~Điều kiện "đã mua mới được đánh giá"~~ | ~~[ADR-0005](DECISIONS.md)~~ — **đã đảo ngược**, xem [ADR-0006](DECISIONS.md) và bước 2.11–2.12 |
