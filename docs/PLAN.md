# Kế hoạch công việc

> Cập nhật: 2026-08-20 · Nhánh làm việc: `develop`

## Đang triển khai — Bỏ luồng duyệt sản phẩm

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
- [ ] **1.2** [core/models.py:20](../grocerly/core/models.py#L20) — rút `STATUS` còn
      `draft` / `published` / `disabled`
- [ ] **1.3** [core/models.py:213](../grocerly/core/models.py#L213) — `default='in_review'`
      → `default='draft'`
- [ ] **1.4** Migration `AlterField` + **data migration**: `in_review` → `draft`,
      `rejected` → `disabled` (giữ nguyên trạng thái ẩn, không sản phẩm nào tự lên sàn)

### Giai đoạn 2 — Luồng đăng sản phẩm

- [ ] **2.1** [useradmin/views.py:89](../grocerly/useradmin/views.py#L89) — bỏ
      `product_status = 'published'` cứng, đọc từ nút bấm (`request.POST.get('action')`),
      **whitelist** giá trị hợp lệ để không nhận bừa từ client
- [ ] **2.2** [add-products.html:157](../grocerly/templates/useradmin/add-products.html#L157)
      — tách nút "Tạo sản phẩm" thành **"Lưu nháp"** + **"Đăng bán"**
- [ ] **2.3** [edit-products.html:176](../grocerly/templates/useradmin/edit-products.html#L176)
      — tương tự, thêm **"Ngừng bán"** (→ `disabled`)
- [ ] **2.4** `edit_product` hiện **không đụng** tới `product_status` → phải bổ sung xử
      lý, nếu không nút mới sẽ vô tác dụng

### Giai đoạn 3 — Bịt lỗ rò hàng nháp

Trước đây mọi sản phẩm đều được đặt thẳng `published` nên không ai để ý. Khi có `draft`
thật, đây thành lỗi thấy được. Chi tiết: [SECURITY.md](SECURITY.md) mục S-04.

- [ ] **3.1** [store_api/views.py:11](../grocerly/store_api/views.py#L11) —
      `ProductListAPI` bổ sung `product_status='published'`
- [ ] **3.2** [store_api/views.py:21](../grocerly/store_api/views.py#L21)
      (`search_products`) và `get_bestsellers` — cùng lỗi; nếu không sửa, **chatbot sẽ
      tư vấn khách mua sản phẩm chưa đăng bán**
- [ ] **3.3** *(Tùy chọn, khuyến nghị)* Gom điều kiện hiển thị vào
      `Product.objects.published()` thay cho 9 lần lặp `filter(product_status='published')`
      — đúng DRY và tránh tái diễn đúng lỗi 3.1

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

- [ ] **5.1** Nhân viên lưu nháp → khách vãng lai **không** thấy ở trang chủ / cửa hàng /
      tìm kiếm
- [ ] **5.2** Nháp **không** xuất hiện ở `/api/v1/products/` và chatbot không gợi ý
- [ ] **5.3** Bấm "Đăng bán" → lên sàn ngay, không cần Admin
- [ ] **5.4** Sản phẩm cũ đang `published` **không** đổi trạng thái sau migration

---

## Backlog theo thứ tự ưu tiên

| # | Việc | Mức | Ghi chú |
|---|---|---|---|
| A | Vá lỗ hổng `payment_completed_view` tự set `paid_status=True` | 🔴 | [S-01](SECURITY.md) — mâu thuẫn trực tiếp yêu cầu phi chức năng mục 1.2.2 của báo cáo |
| B | `add_to_cart` đọc giá từ DB thay vì query string | 🔴 | [S-02](SECURITY.md) |
| C | Giới hạn truy cập `/api/v1/chat/` | 🟠 | [S-03](SECURITY.md) — hiện ai cũng đốt được quota Gemini |
| D | Sửa/Xóa đánh giá sản phẩm | 🟠 | Báo cáo có (UC 3.2.14, Hình 22–23), code không — [SPEC-GAPS](SPEC-GAPS.md) |
| E | Điều kiện "đã mua mới được đánh giá" | 🟠 | Báo cáo yêu cầu, code chỉ chặn trùng lặp |
| F | Actor generalization + đổi thuật ngữ Vendor | 🟡 | [ADR-0001](DECISIONS.md), [ADR-0003](DECISIONS.md) |
| G | Bổ sung test case AI Chatbot + VNPay vào chương 4 | 🟡 | Hiện chỉ có 5 TC, không TC nào cho 2 điểm nhấn của đề tài |
| H | Sửa lỗi đánh số mục/hình trong báo cáo | 🟡 | Trùng số mục 3.5; Hình trang 92 ghi sai "Hình 3.5.23" |
| I | Nối dây filter "Status" ở trang sản phẩm | 🔵 | [products.html:22](../grocerly/templates/useradmin/products.html#L22) là UI chết — `<select>` không có `name`, không nằm trong form |
| J | Phân trang danh sách sản phẩm | 🔵 | Báo cáo UC 3.2.3 có nhắc, code không có |
| K | Đổi mật khẩu 3 tài khoản mẫu in ở trang 108 báo cáo | 🔴 | Sau khi bảo vệ xong — repo public + site đang chạy thật |

Mức độ: 🔴 nghiêm trọng · 🟠 lệch đặc tả · 🟡 tài liệu · 🔵 cải thiện

---

## Không làm (đã cân nhắc và loại)

| Việc | Lý do loại |
|---|---|
| Cài đầy đủ luồng duyệt sản phẩm | [ADR-0002](DECISIONS.md) — sai mô hình nghiệp vụ |
| Chuyển quyền tạo sản phẩm lên Admin | Đúng ngành hơn nhưng kéo theo sửa quá nhiều use case ở giai đoạn sắp bảo vệ |
| Refactor `useradmin` để scope theo vendor | Không cần nữa nếu chấp nhận [ADR-0003](DECISIONS.md) |
| Chuyển giỏ hàng từ session sang model | Session hoạt động tốt, cho phép khách vãng lai mua hàng; đổi sẽ phá nhiều sequence diagram |
| Commit thư mục `.claude/` vào repo | [ADR-0004](DECISIONS.md) |
