# 01 — Bỏ quy trình duyệt sản phẩm khỏi báo cáo

**Lý do:** [ADR-0002](../DECISIONS.md). Code đã bỏ hẳn hai trạng thái `in_review` và
`rejected` (migration `0005`, đã áp lên production 2026-08-24). Nhân viên tự bấm
**"Lưu nháp"** hoặc **"Đăng bán"**, không qua bước Quản trị viên duyệt.

**Trạng thái hợp lệ hiện tại của sản phẩm:** `draft` (Nháp) · `published` (Đang bán) ·
`disabled` (Ngừng bán).

| # | Vị trí | Việc |
|---|---|---|
| 4.1 | UC 3.2.19, tr.27 | Sửa Main Flow |
| 4.2 | UC 3.2.24, tr.31 | Bỏ quyền "Duyệt bài" của Quản trị viên |
| 4.3 | Mục 3.3.24a + Hình 40 | Xóa hẳn, đánh số lại hình |
| 4.4 | Hình 28, Hình 29 | Sửa sơ đồ tuần tự |
| 4.5 | Bảng 30, tr.57 | Sửa giá trị hợp lệ của `product_status` |
| 4.6 | Hình 4 | Bỏ liên kết use case "Duyệt sản phẩm" |

---

## 4.1 — UC 3.2.19 (tr.27)

**Bỏ:** vế mô tả sản phẩm được lưu ở trạng thái *"In Review"* / *"Chờ duyệt"* và phải
đợi Quản trị viên phê duyệt.

**Thay bằng:**

```
Main Flow:
1. Nhân viên chọn chức năng "Thêm sản phẩm" trên trang quản trị.
2. Hệ thống hiển thị biểu mẫu nhập thông tin sản phẩm.
3. Nhân viên nhập tên, mô tả, giá bán, giá cũ, số lượng tồn kho, danh mục,
   nhà cung cấp, hình ảnh chính và các hình ảnh phụ.
4. Nhân viên chọn một trong hai thao tác:
   a. "Lưu nháp"  — sản phẩm được lưu ở trạng thái Nháp (draft).
   b. "Đăng bán"  — sản phẩm được lưu ở trạng thái Đang bán (published).
5. Hệ thống kiểm tra dữ liệu hợp lệ, lưu sản phẩm kèm trạng thái tương ứng
   và chuyển về danh sách sản phẩm.

Post-Conditions:
- Sản phẩm ở trạng thái Đang bán hiển thị ngay trên cửa hàng, trong kết quả
  tìm kiếm và với trợ lý AI.
- Sản phẩm ở trạng thái Nháp không hiển thị với khách hàng ở bất kỳ đâu.

Alternate Flow:
- Nếu nhân viên gửi biểu mẫu mà không chọn thao tác nào, hệ thống mặc định
  lưu ở trạng thái Nháp để sản phẩm chưa hoàn thiện không vô tình lên sàn.
```

**Ghi chú để trả lời phản biện nếu bị hỏi *"sao không có kiểm duyệt?"*:**

```
Grocerly là mô hình một siêu thị với nhân viên nội bộ, không phải sàn thương
mại điện tử nhiều người bán. Người đăng sản phẩm là nhân viên có hợp đồng lao
động, chịu trách nhiệm trực tiếp với chủ hệ thống, nên khâu kiểm duyệt chỉ tạo
thêm ma sát vận hành mà không giảm rủi ro. Các nền tảng bán lẻ một chủ như
WooCommerce và Shopify cũng dùng mô hình Nháp/Đang bán do chính người đăng
kiểm soát, không có luồng phê duyệt.
```

---

## 4.2 — UC 3.2.24 (tr.31)

**Bỏ:** vế *"Duyệt bài"* và *"thay đổi Status (Duyệt thành Published / Khóa thành
Rejected)"*.

**Giữ:** quyền gỡ sản phẩm vi phạm của Quản trị viên.

**Thay bằng:**

```
Quản trị viên có toàn quyền trên dữ liệu sản phẩm, bao gồm chuyển một sản phẩm
sang trạng thái Ngừng bán (disabled) để gỡ khỏi cửa hàng khi phát hiện sai
phạm về thông tin, giá hoặc hình ảnh. Đây là thao tác xử lý sự cố sau khi sản
phẩm đã lên sàn, không phải cổng phê duyệt trước khi đăng.
```

---

## 4.3 — Mục 3.3.24a và Hình 40

**Xóa hẳn** mục 3.3.24a cùng **Hình 40** (sơ đồ tuần tự "Duyệt sản phẩm").

Sau khi xóa: **đánh số lại Hình 41 → Hình 40**, và toàn bộ hình phía sau lùi một số.
Nhớ cập nhật cả **Danh mục hình ảnh** ở đầu báo cáo và mọi câu trích dẫn *"xem Hình N"*
trong thân bài.

> Làm bước này **sau cùng** trong nhóm 01, vì nó xê dịch số thứ tự của mọi hình phía sau.

---

## 4.4 — Hình 28 và Hình 29

**Hình 28** (sơ đồ tuần tự Thêm sản phẩm): bỏ nhánh/nhãn *"trạng thái Chờ duyệt"*. Luồng
đúng là nhân viên chọn thao tác, hệ thống lưu thẳng trạng thái tương ứng:

```
Nhân viên → Giao diện: nhập thông tin, bấm "Lưu nháp" hoặc "Đăng bán"
Giao diện → useradmin.views.add_product: POST kèm tham số action
add_product → add_product: quy đổi action sang product_status qua danh sách
              hợp lệ (save_draft→draft, publish→published, disable→disabled)
add_product → CSDL: INSERT sản phẩm với product_status tương ứng
CSDL → add_product: xác nhận
add_product → Giao diện: chuyển hướng về danh sách sản phẩm
```

**Hình 29**: câu lệnh UPDATE đang ghi `status="in_review"`. Sửa thành:

```
UPDATE core_product SET product_status = 'published' WHERE p_id = ...
```

---

## 4.5 — Bảng 30 (tr.57)

Dòng `product_status` trong bảng mô tả bảng `core_product`:

```
Tên trường:   product_status
Kiểu dữ liệu: varchar(10)
Ràng buộc:    NOT NULL, mặc định 'draft'
Mô tả:        Trạng thái đăng bán của sản phẩm. Nhận một trong ba giá trị:
              'draft' (Nháp — chỉ nhân viên thấy),
              'published' (Đang bán — hiển thị với khách hàng),
              'disabled' (Ngừng bán — đã gỡ khỏi cửa hàng).
```

> ⚠️ Bảng `core_cartorder` và `core_cartorderitem` **cũng có** trường tên
> `product_status`, nhưng mang nghĩa **trạng thái giao hàng**
> (`processing`/`shipped`/`delivered`). Khi sửa Bảng 30 đừng sửa nhầm sang hai bảng đó.

---

## 4.6 — Hình 4 (Sơ đồ Use Case tổng quát)

Bỏ use case **"Duyệt sản phẩm"** và đường liên kết từ tác nhân Quản trị viên tới nó.

Nếu bạn làm luôn mục **F** ([03-tac-nhan-va-thuat-ngu.md](03-tac-nhan-va-thuat-ngu.md))
thì sửa Hình 4 một lần cho cả hai việc, vì cùng đụng vào sơ đồ này.
