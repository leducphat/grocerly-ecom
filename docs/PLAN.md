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

`main` đang chậm **24 commit**. Production vẫn chạy code có S-01/S-02 khai thác được —
mọi bản vá đã làm **chưa bảo vệ được gì**.

**Quyết định 2026-08-26: hoãn.** Production đang chạy ổn định và chưa cần demo cho GVHD,
nên người thực hiện đồ án chọn để nguyên và tích lũy thêm thay đổi. Đây là **đánh đổi có
ý thức**, không phải quên: đổi lại là mọi bản vá bảo mật vẫn chỉ nằm trên `develop`.

Hệ quả cần nhớ khi deploy:

- `build.sh` chạy `compilemessages` nên `django.mo` được biên dịch lại — mọi chuỗi tiếng
  Việt thêm từ 2026-08-25 tới nay **chỉ hiện đúng sau bước này** (xem *Bẫy i18n* bên dưới)
- Migration `0006_drop_stripe_payment_intent` sẽ chạy và drop cột thật trên Neon
- Trước khi deploy nên soát đơn hàng mắc kẹt ở trạng thái rác:
  `CartOrder.objects.exclude(product_status__in=['processing','shipped','delivered'])`
  — xem bước 2.2

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
| **2.5** | `except:` trần ([S-07](SECURITY.md)) + `SECRET_KEY`/`DEBUG` ([S-05](SECURITY.md)) | mục 1.2.2 Yêu cầu phi chức năng | thấp |
| **2.6** | **Tầng unit test** — xem bảng riêng bên dưới | Chương 4 — hai điểm nhấn chưa có test nào | trung bình |
| **2.7** | Nhập mã vận đơn ở `useradmin` ([A9](SPEC-GAPS.md)) | UC 3.2.20 Alternate Flow | trung bình |
| **2.8** | Phân trang ([A3](SPEC-GAPS.md)) | UC 3.2.3 Alternate Flow | trung bình |
| **2.9** | Coupon hạn dùng + số lượt ([A6](SPEC-GAPS.md)) | UC 3.2.21 | trung bình, có migration |
| **2.10** | Hủy đơn ([A7](SPEC-GAPS.md)) | UC 3.2.25 | trung bình-cao, có migration |
| **2.11** | **Khóa ngoại `CartOrderItem` → `Product`** | [ADR-0006](DECISIONS.md); vá nợ kỹ thuật #6 | cao, đụng checkout |
| **2.12** | Điều kiện đã mua mới đánh giá ([A2](SPEC-GAPS.md)) | UC 3.2.14 + **Hình 21** | phụ thuộc 2.11 |
| **2.13** | Gửi email hàng loạt ([A10](SPEC-GAPS.md)) | UC 3.2.22 Alternate Flow | cao, cần cấu hình SMTP |
| **2.14** | Các endpoint đổi dữ liệu bằng GET còn lại ([S-10](SECURITY.md)) + cờ `Secure` cho cookie ([S-11](SECURITY.md)) | mục 1.2.2 Yêu cầu phi chức năng | thấp-trung bình |

**Ghi chú 2.4:** hôm 2026-08-25 mục này còn treo vì chưa biết báo cáo có mô tả cột đó
không. Đã đọc bản gốc: **ERD Hình 45 và Bảng 32 đều không có** `stripe_payment_intent`.
Nên drop cột làm code **khớp** báo cáo, không phải ngược lại. Đã kiểm production: 11 đơn
hàng, **0 đơn có dữ liệu** ở cột này.

**Ghi chú 2.11:** giỏ hàng đã lưu `pid` trong session nên `save_checkout_info` tra ngược
được sản phẩm, không phải đổi cấu trúc giỏ. Migration cần **backfill theo tên** cho dữ
liệu cũ; dòng nào không khớp để `NULL`.

### 2.6 — Tầng unit test (mở rộng 2026-08-26)

Ban đầu mục này chỉ là *"unit test VNPay"*. Rà lại thì vấn đề rộng hơn: 49 test có sẵn
**đều là test hồi quy ở mức HTTP** (`django.test.TestCase` + `self.client`), đúng mục
đích của chúng, nhưng **không có tầng unit test nào** dưới đó. Grep xác nhận `safe_float`,
`vnd`, `vnpay.*`, `SoftDeleteModel.*`, hai middleware — tất cả 0 lần xuất hiện trong test.

Thứ tự trong nhóm là đường găng: **2.6a → 2.6d → 2.6f**. Ba mục này đã xong.

| | Việc | Vì sao | Trạng thái |
|---|---|---|---|
| **2.6a** | `core/vnpay.py` — ký, sort, bỏ giá trị rỗng, URL-encode; `validate_response` với chữ ký đúng/sai/thiếu | Hàm thuần, không DB. Điểm nhấn thứ hai của đề tài mà [C7](SPEC-GAPS.md) ghi là không có TC nào | ✅ **Xong 2026-08-26** — 18 test |
| **2.6b** | `safe_float` / `safe_int` | Nằm trên đường tiền. Hành vi **đang sai so với mô tả** — xem ghi chú dưới | chưa làm |
| **2.6c** | Filter `vnd` / `mul` | Hiển thị trên **mọi** trang có giá | chưa làm |
| **2.6d** | `SoftDeleteModel` + cascade/restore của `Vendor` | Chốt **Bẫy #3** thành test; là tiền đề của 2.1 | ✅ **Xong 2026-08-26** — 14 test, phát hiện lỗi thật |
| **2.6e** | `RestrictStaffMiddleware` (**Bẫy #6**), `ForceDefaultLanguageMiddleware` | Thứ tự middleware bắt buộc mà không gì bảo vệ | chưa làm |
| **2.6f** | `save_checkout_info` — tạo đơn, tạo `CartOrderItem`, luồng đơn treo | **Tiền đề bắt buộc của 2.11**: bước đó viết lại đúng hàm này | ✅ **Xong 2026-08-26** — 26 test, nhóm `CartOrderItemSnapshotTests` ghi rõ cái gì 2.11 được đổi |
| **2.6g** | `userauths` — đăng ký, đăng nhập, redirect theo vai trò | `userauths/tests.py` đang là stub rỗng | chưa làm |

**Ghi chú 2.6b** — đã dò thử, chưa sửa. `safe_float` trả `0.0` cho `'1.000.000,50'` (định
dạng tiền Việt có phần thập phân, đúng thứ hàm này tự nhận là xử lý) và cho `'1,234.56'`;
`'-5'` ra `5.0` (mất dấu âm); `1e16` ra `116.0`. **Là lỗi tiềm ẩn, không phải đang khai
thác được**: sau bản vá [S-02](SECURITY.md), giá vào session là `float` đọc từ database
nên không đi qua nhánh hỏng. Nhưng hàm vẫn nằm trên đường tiền (`save_checkout_info` đọc
giá từ session qua nó) và **không có gì chốt lại hành vi đó**.

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

- [ ] **4.1** Chương/mục **rà soát bảo mật** — **11 lỗ hổng** ở [SECURITY.md](SECURITY.md),
      kịch bản khai thác, cách vá, và cái gì **cố ý không vá** kèm lý do.
      Phần đáng giá nhất không phải danh sách lỗi mà là mục *Rà soát 2026-08-26*: **ba
      phát hiện ban đầu bị bác bỏ** khi có bước phản biện độc lập. Thấy `@csrf_exempt`
      trong code **chưa đủ để kết luận có lỗ hổng** — còn phải trả lời được request của
      kẻ tấn công có mang được cookie phiên tới không, mà điều đó phụ thuộc `SameSite`
- [ ] **4.2** Viết lại **Chương 4** — từ 5 test case thủ công lên **174 test tự động**
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
