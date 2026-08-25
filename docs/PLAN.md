# Kế hoạch công việc

> Cập nhật: 2026-08-25 · Nhánh làm việc: `develop`

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

- [ ] **1.1** Merge `develop` → `main`, Render tự deploy

`main` đang chậm **16 commit**. Production vẫn chạy code có S-01/S-02 khai thác được —
mọi bản vá đã làm **chưa bảo vệ được gì**. Deploy cũng xử lý luôn `django.mo`
(`build.sh` có `compilemessages`) nên các chuỗi tiếng Việt mới sẽ hiện đúng.

Việc rẻ nhất và đang treo lâu nhất trong toàn bộ kế hoạch.

## Giai đoạn 2 — Code đóng khoảng cách báo cáo↔code

Xếp theo tỉ lệ giá trị/chi phí. Cột **Neo** là chỗ báo cáo **đã mô tả sẵn** — làm xong
là đóng gap mà không phải sửa báo cáo.

| | Việc | Neo trong báo cáo | Chi phí |
|---|---|---|---|
| **2.1** | `delete_product` xóa mềm khi có đơn liên quan ([B3](SPEC-GAPS.md)) | **Hình 30 đã vẽ sẵn đúng nhánh này** | thấp |
| **2.2** | Chặn đổi trạng thái khi đơn đã `delivered` ([A8](SPEC-GAPS.md)) | UC 3.2.20 Exception Flow | thấp |
| **2.3** | Làm sạch giỏ hàng ([A4](SPEC-GAPS.md)) | UC 3.2.6 Alternate Flow | thấp |
| **2.4** | Drop cột `stripe_payment_intent` | ERD + Bảng 32 **không có** cột này | thấp |
| **2.5** | `except:` trần ([S-07](SECURITY.md)) + `SECRET_KEY`/`DEBUG` ([S-05](SECURITY.md)) | mục 1.2.2 Yêu cầu phi chức năng | thấp |
| **2.6** | Unit test VNPay (`core/vnpay.py`) | Chương 4 — điểm nhấn thứ hai chưa có test nào | trung bình |
| **2.7** | Nhập mã vận đơn ở `useradmin` ([A9](SPEC-GAPS.md)) | UC 3.2.20 Alternate Flow | trung bình |
| **2.8** | Phân trang ([A3](SPEC-GAPS.md)) | UC 3.2.3 Alternate Flow | trung bình |
| **2.9** | Coupon hạn dùng + số lượt ([A6](SPEC-GAPS.md)) | UC 3.2.21 | trung bình, có migration |
| **2.10** | Hủy đơn ([A7](SPEC-GAPS.md)) | UC 3.2.25 | trung bình-cao, có migration |
| **2.11** | **Khóa ngoại `CartOrderItem` → `Product`** | [ADR-0006](DECISIONS.md); vá nợ kỹ thuật #6 | cao, đụng checkout |
| **2.12** | Điều kiện đã mua mới đánh giá ([A2](SPEC-GAPS.md)) | UC 3.2.14 + **Hình 21** | phụ thuộc 2.11 |
| **2.13** | Gửi email hàng loạt ([A10](SPEC-GAPS.md)) | UC 3.2.22 Alternate Flow | cao, cần cấu hình SMTP |

**Ghi chú 2.4:** hôm 2026-08-25 mục này còn treo vì chưa biết báo cáo có mô tả cột đó
không. Đã đọc bản gốc: **ERD Hình 45 và Bảng 32 đều không có** `stripe_payment_intent`.
Nên drop cột làm code **khớp** báo cáo, không phải ngược lại. Đã kiểm production: 11 đơn
hàng, **0 đơn có dữ liệu** ở cột này.

**Ghi chú 2.11:** giỏ hàng đã lưu `pid` trong session nên `save_checkout_info` tra ngược
được sản phẩm, không phải đổi cấu trúc giỏ. Migration cần **backfill theo tên** cho dữ
liệu cũ; dòng nào không khớp để `NULL`.

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

- [ ] **4.1** Chương/mục **rà soát bảo mật** — 8 lỗ hổng ở [SECURITY.md](SECURITY.md),
      kịch bản khai thác, cách vá, và cái gì **cố ý không vá** kèm lý do
- [ ] **4.2** Viết lại **Chương 4** — từ 5 test case thủ công lên 49 test tự động, cộng
      bảng test case cho AI Chatbot và VNPay
- [ ] **4.3** Mục **quyết định kiến trúc** dựa trên 6 ADR, có cả phương án đã loại và lý
      do. Cặp ADR-0005 → ADR-0006 là ví dụ tốt: cùng dữ kiện kỹ thuật, hai kết luận khác
      nhau vì ràng buộc dự án khác nhau
- [ ] **4.4** Cập nhật **Kết luận** — mục *Nhược điểm* và *Hướng phát triển* phải phản
      ánh trạng thái mới, không bê nguyên từ bản Tiểu luận

---

## Đã xong

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
