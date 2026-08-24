# Kế hoạch công việc

> Cập nhật: 2026-08-24 · Nhánh làm việc: `develop`

## Đang triển khai — Bỏ luồng duyệt sản phẩm

> **Trạng thái 2026-08-24:** Giai đoạn 1–3 và 5 đã xong ở phía code (27 test xanh).
> Còn lại **bước 1.1** và **áp migration lên production** — cả hai cần người dùng cho
> phép vì `.env` trỏ vào database thật. **Giai đoạn 4** là sửa file báo cáo, làm thủ công.

Quyết định và lý do: [ADR-0002](DECISIONS.md#adr-0002--bỏ-quy-trình-duyệt-sản-phẩm-in_review).

**Phạm vi ảnh hưởng hẹp:** `Product.product_status` chỉ được **ghi ở đúng một chỗ**
([useradmin/views.py:89](../grocerly/useradmin/views.py#L89)); 9 chỗ đọc trong
[core/views.py](../grocerly/core/views.py) đều lọc `='published'` nên **không phải sửa**.

> ⚠️ `CartOrder` và `CartOrderItem` cũng có field tên `product_status` nhưng là trạng
> thái giao hàng. **Không tìm-thay-thế toàn cục.**

### Giai đoạn 1 — Model & dữ liệu

- [ ] **1.1** Đếm sản phẩm theo từng `product_status` trên Neon (chỉ SELECT) — biết bao
      nhiêu bản ghi đang `in_review`/`rejected` cần chuyển. *Cần người dùng cho phép,
      vì `.env` trỏ vào database production.*
- [x] **1.2** [core/models.py](../grocerly/core/models.py) — `STATUS` còn
      `draft` / `published` / `disabled`
- [x] **1.3** `Product.product_status` — `default='draft'`
- [x] **1.4** [0005_product_status_drop_review_flow.py](../grocerly/core/migrations/0005_product_status_drop_review_flow.py)
      — `AlterField` + data migration `in_review` → `draft`, `rejected` → `disabled`.
      **Chưa áp lên production.** Chiều lùi là no-op có chủ ý: hai giá trị cũ gộp vào
      trạng thái đã tồn tại nên không tách ngược được.

### Giai đoạn 2 — Luồng đăng sản phẩm

- [x] **2.1** `add_product` đọc nút bấm qua `resolve_product_status()`, whitelist
      `PRODUCT_STATUS_ACTIONS`. Mặc định `draft` khi thiếu/lạ giá trị
- [x] **2.2** [add-products.html](../grocerly/templates/useradmin/add-products.html) —
      **"Đăng bán"** + **"Lưu nháp"**
- [x] **2.3** [edit-products.html](../grocerly/templates/useradmin/edit-products.html) —
      nút đổi trạng thái hiện theo trạng thái hiện tại (không hiện "Đăng bán" cho sản
      phẩm đang bán), kèm dòng hiển thị trạng thái hiện tại
- [x] **2.4** `edit_product` giữ nguyên `product_status` khi bấm "Lưu thay đổi"; chỉ đổi
      khi bấm đúng nút trạng thái

### Giai đoạn 3 — Bịt lỗ rò hàng nháp

Trước đây mọi sản phẩm đều được đặt thẳng `published` nên không ai để ý. Khi có `draft`
thật, đây thành lỗi thấy được. Chi tiết: [SECURITY.md](SECURITY.md) mục S-04.

- [x] **3.1** `ProductListAPI` → `Product.objects.published().filter(status=True, in_stock=True)`
- [x] **3.2** `search_products` và `get_bestsellers` — cùng cách
- [x] **3.3** `ProductQuerySet.published()` + `ProductManager` trong
      [core/models.py](../grocerly/core/models.py). **12** chỗ lặp
      `filter(product_status='published')` nay gom về một định nghĩa duy nhất

### Giai đoạn 4 — Cập nhật báo cáo

- [ ] **4.1** UC 3.2.19 (tr.27): *"Lưu dạng In Review"* → *"Lưu nháp hoặc đăng bán ngay"*
- [ ] **4.2** UC 3.2.24 (tr.31): bỏ vế *"Duyệt bài"* và *"thay đổi Status (Duyệt thành
      Published / Khóa thành Rejected)"*; giữ quyền gỡ sản phẩm vi phạm
- [ ] **4.3** Bỏ mục 3.3.24a + **Hình 40**; đánh số lại Hình 41→40 và toàn bộ hình sau đó
- [ ] **4.4** Hình 28: bỏ *"trạng thái Chờ duyệt"*; Hình 29: sửa `status="in_review"`
      trong câu UPDATE
- [ ] **4.5** Bảng 30 (tr.57), dòng `product_status`: cập nhật giá trị hợp lệ
- [ ] **4.6** Hình 4: bỏ liên kết duyệt sản phẩm của Quản trị viên

### Giai đoạn 5 — Kiểm thử

Đã tự động hóa thay cho kiểm thử tay — chạy `python manage.py test --settings=grocerly.settings_test`:

- [x] **5.1** `DraftProductVisibilityTests` — nháp không ra tìm kiếm, trang danh mục, và
      không thêm được vào giỏ
- [x] **5.2** `store_api.tests.DraftLeakTests` — nháp không ra `/api/v1/products/`,
      `search_products`, `get_bestsellers`
- [x] **5.3** `useradmin.tests.AddProductStatusTests` — "Đăng bán" lên sàn ngay, không
      cần Admin; nút lạ hoặc thiếu thì về `draft`
- [x] **5.4** `ProductStatusMigrationTests` — `published`/`draft` không đổi,
      `in_review`→`draft`, `rejected`→`disabled`

---

## Backlog theo thứ tự ưu tiên

| # | Việc | Mức | Ghi chú |
|---|---|---|---|
| ~~A~~ | ~~Vá lỗ hổng `payment_completed_view` tự set `paid_status=True`~~ | ✅ | Xong 2026-08-24 — [S-01](SECURITY.md) |
| ~~B~~ | ~~`add_to_cart` đọc giá từ DB thay vì query string~~ | ✅ | Xong 2026-08-24 — [S-02](SECURITY.md), đóng luôn A5 của [SPEC-GAPS](SPEC-GAPS.md) |
| C | Giới hạn truy cập `/api/v1/chat/` | 🟠 | [S-03](SECURITY.md) — hiện ai cũng đốt được quota Gemini |
| D | Sửa/Xóa đánh giá sản phẩm | 🟠 | Báo cáo có (UC 3.2.14, Hình 22–23), code không — [SPEC-GAPS](SPEC-GAPS.md) |
| E | Điều kiện "đã mua mới được đánh giá" | 🟠 | Báo cáo yêu cầu ([A2](SPEC-GAPS.md)); chốt chặn trùng lặp đã chuyển về server ở [S-08](SECURITY.md) nhưng điều kiện đã mua thì chưa có |
| F | Actor generalization + đổi thuật ngữ Vendor | 🟡 | [ADR-0001](DECISIONS.md), [ADR-0003](DECISIONS.md) |
| G | Bổ sung test case AI Chatbot + VNPay vào chương 4 | 🟡 | Hiện chỉ có 5 TC, không TC nào cho 2 điểm nhấn của đề tài |
| H | Sửa lỗi đánh số mục/hình trong báo cáo | 🟡 | Trùng số mục 3.5; Hình trang 92 ghi sai "Hình 3.5.23" |
| I | Nối dây filter "Status" ở trang sản phẩm | 🔵 | [products.html:22](../grocerly/templates/useradmin/products.html#L22) là UI chết — `<select>` không có `name`, không nằm trong form |
| J | Phân trang danh sách sản phẩm | 🔵 | Báo cáo UC 3.2.3 có nhắc, code không có |
| K | Đổi mật khẩu 3 tài khoản mẫu in ở trang 108 báo cáo | 🔴 | Sau khi bảo vệ xong — repo public + site đang chạy thật |
| L | Quyết định về cột `cartorder.stripe_payment_intent` | 🟡 | Field đã bị bỏ khỏi model từ commit `0925f27` nhưng **chưa từng có migration**, nên cột vẫn còn trên production. `makemigrations` sẽ luôn đòi tạo `RemoveField`. Cố ý **không** gộp vào migration 0005: đó là lệnh `DROP COLUMN` trên dữ liệu thật, phải là quyết định riêng |

Mức độ: 🔴 nghiêm trọng · 🟠 lệch đặc tả · 🟡 tài liệu · 🔵 cải thiện

---

## Đã xong

### 2026-08-24 — Vá ba lỗ hổng nghiệp vụ

Backlog **A** + **B** + [S-08](SECURITY.md#s-08--chốt-chặn-đánh-giá-chỉ-nằm-ở-template)
(phát hiện thêm trong lúc rà), kèm mục **A5** của [SPEC-GAPS](SPEC-GAPS.md).
Chỉ chạm `core/views.py` — **không sửa model, không migration**, nên không sequence
diagram nào của báo cáo bị lệch.

Kèm theo:

- [core/tests.py](../grocerly/core/tests.py) — 12 test hồi quy, tái hiện đúng kịch bản
  khai thác. Chạy trên code cũ: 9 đỏ. Đây là **test tự động đầu tiên** của dự án.
- [grocerly/settings_test.py](../grocerly/grocerly/settings_test.py) — ép SQLite
  in-memory. Cần thiết vì `.env` trỏ DB production: `manage.py test` với settings mặc
  định sẽ tạo database `test_*` **trên Neon**.

```bash
cd grocerly
python manage.py test core --settings=grocerly.settings_test
```

Việc này **đóng góp được cho mục G** của backlog (báo cáo chương 4 chỉ có 5 test case):
12 test case tự động cho luồng giỏ hàng / thanh toán / đánh giá.

---

## Không làm (đã cân nhắc và loại)

| Việc | Lý do loại |
|---|---|
| Cài đầy đủ luồng duyệt sản phẩm | [ADR-0002](DECISIONS.md) — sai mô hình nghiệp vụ |
| Chuyển quyền tạo sản phẩm lên Admin | Đúng ngành hơn nhưng kéo theo sửa quá nhiều use case ở giai đoạn sắp bảo vệ |
| Refactor `useradmin` để scope theo vendor | Không cần nữa nếu chấp nhận [ADR-0003](DECISIONS.md) |
| Chuyển giỏ hàng từ session sang model | Session hoạt động tốt, cho phép khách vãng lai mua hàng; đổi sẽ phá nhiều sequence diagram |
| Commit thư mục `.claude/` vào repo | [ADR-0004](DECISIONS.md) |
