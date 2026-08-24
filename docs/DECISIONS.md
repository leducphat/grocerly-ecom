# Nhật ký quyết định kiến trúc (ADR)

Mỗi mục ghi lại **một quyết định**, bối cảnh dẫn tới nó và hệ quả. Mục đích: sáu tháng
sau đọc lại vẫn hiểu *tại sao* code lại như vậy, thay vì phải suy đoán.

Trạng thái: `Đã chốt` · `Đề xuất` · `Thay thế bởi ADR-XXXX`

---

## ADR-0001 — Giữ hai vai trò Quản trị viên và Nhân viên

**Trạng thái:** Đã chốt · 2026-08-20

### Bối cảnh

Quyền của Admin đang **bao trùm hoàn toàn** quyền của Staff: `admin_required` chấp nhận
cả `is_superuser` lẫn `is_staff`, và Admin còn có Django Admin console chỉnh được mọi
thứ. Câu hỏi đặt ra: hai vai trò chồng lấn như vậy có thừa không?

### Quyết định

**Giữ cả hai.** Overlap kiểu bao hàm là phân cấp vai trò bình thường, không phải lỗi
thiết kế. Ranh giới nằm ở **phạm vi thẩm quyền**, không ở khả năng kỹ thuật:

| | Nhân viên | Quản trị viên |
|---|---|---|
| Sản phẩm, tồn kho, đơn hàng | ✔ | ✔ (kế thừa) |
| Quản lý người dùng & phân quyền | ✘ | ✔ |
| Danh mục dùng chung | ✘ | ✔ |
| Mã giảm giá | ✘ | ✔ |
| Gỡ sản phẩm vi phạm, xem toàn bộ doanh thu | ✘ | ✔ |

### Lý do

1. **Đặc quyền tối thiểu** — nhân viên chạy ca không nên xóa được tài khoản hay đổi
   cấu hình thanh toán. Giảm thiệt hại khi lộ tài khoản.
2. **Truy vết trách nhiệm** — biết ai đổi giá, ai đổi trạng thái đơn.
3. **Trải nghiệm vận hành** — Django Admin quá tổng quát để xử lý đơn hàng hàng ngày;
   `useradmin` tối giản cho tác vụ lặp lại. Đây là lý do mạnh nhất cho việc tồn tại
   hai giao diện.
4. Đối chiếu thực tế: WooCommerce có role `Shop Manager`, Shopify có `Staff accounts`,
   Magento có ACL role — đều là quan hệ bao hàm với vai trò chủ hệ thống.

### Hệ quả

- Trong sơ đồ Use Case phải dùng **generalization giữa tác nhân** (Quản trị viên ─▷
  Nhân viên), **không** nhân đôi use case theo từng tác nhân.
- Quy tắc mô hình hóa: *hai use case có cùng Main Flow là một use case; khác tác nhân
  không sinh ra use case mới, khác luồng xử lý mới sinh ra.*
- Cần bổ sung generalization này vào Hình 4 của báo cáo (hiện đã áp dụng đúng cho cặp
  Khách hàng ─▷ Khách vãng lai, chỉ thiếu cặp còn lại).

---

## ADR-0002 — Bỏ quy trình duyệt sản phẩm (`in_review`)

**Trạng thái:** Đã chốt · 2026-08-20 · Triển khai: [PLAN.md](PLAN.md) giai đoạn 1–3

### Bối cảnh

`Product.STATUS` có 5 giá trị `draft / disabled / in_review / rejected / published`,
mặc định `in_review`. Báo cáo (UC 3.2.19, Hình 28) mô tả nhân viên đăng sản phẩm sẽ ở
trạng thái *"Chờ duyệt"* rồi Admin duyệt. Nhưng code
([useradmin/views.py:89](../grocerly/useradmin/views.py#L89)) đặt thẳng `'published'` —
quy trình duyệt **chưa từng được cài đặt**.

Phải chọn: cài cho đủ, hay bỏ hẳn?

### Quyết định

**Bỏ hẳn.** Rút còn ba trạng thái: `draft` / `published` / `disabled`, mặc định `draft`.

### Lý do

Nguyên tắc: *kiểm duyệt chỉ cần khi người đăng nội dung không chịu trách nhiệm hợp
đồng/pháp lý với chủ hệ thống.*

- **Sàn nhiều người bán** (Shopee, Etsy, Amazon 3P): người bán là bên ngoài, có thể bán
  hàng giả/hàng cấm → bắt buộc kiểm duyệt.
- **Cửa hàng một chủ** (Grocerly): người đăng là nhân viên có hợp đồng lao động, chịu
  trách nhiệm trực tiếp → kiểm duyệt chỉ thêm ma sát mà không giảm rủi ro. Nếu đã tin
  nhân viên đủ để cho họ sửa giá và đổi trạng thái đơn hàng, thì việc đăng sản phẩm
  không nguy hiểm hơn.

Đối chiếu sản phẩm thật: **WooCommerce và Shopify đều không có luồng duyệt sản phẩm.**
Trạng thái họ dùng là Draft/Published/Archived — do chính người đăng kiểm soát.

Chuỗi `in_review → rejected` nhiều khả năng được kế thừa từ template multi-vendor ban
đầu, cùng nguồn gốc với vấn đề `Vendor` ở ADR-0003.

### Phương án đã cân nhắc

| Phương án | Đánh giá |
|---|---|
| Cài đầy đủ luồng duyệt | Thêm 1 use case + 1 sequence diagram để "khoe" trong báo cáo, nhưng tạo ma sát vận hành không có lý do nghiệp vụ |
| **Bỏ, dùng draft/published** ✔ | Khớp best practice và khớp mô hình một cửa hàng |
| Chuyển quyền tạo sản phẩm lên Admin (mô hình merchandising tập trung của bán lẻ thật) | Đúng với ngành nhất, nhưng kéo theo sửa nhiều use case — quá tốn ở giai đoạn sắp bảo vệ |

### Hệ quả

- ADR-0001 vẫn đứng vững: hai vai trò được biện minh bằng **phạm vi thẩm quyền**, không
  phải bằng cổng duyệt.
- Nhân viên tự quyết **khi nào** sản phẩm sẵn sàng (nút "Lưu nháp" / "Đăng bán"), thay vì
  xin phép **có được đăng hay không**.
- Khi có `draft` thật, lỗ rò hàng nháp qua API/chatbot (S-04) trở thành lỗi thấy được →
  phải sửa cùng lượt.
- Báo cáo phải sửa: UC 3.2.19, UC 3.2.24, Hình 28, Hình 29, bỏ Hình 40, Bảng 30.

---

## ADR-0003 — `Vendor` là thương hiệu, không phải người bán có tài khoản

**Trạng thái:** Đề xuất · 2026-08-20

### Bối cảnh

Báo cáo mô tả Grocerly là hệ thống **multi-vendor**, "Người bán (Vendor/Nhân viên cửa
hàng)" đăng nhập để vận hành gian hàng riêng. Nhưng thực tế:

- Dữ liệu bảng `core_vendor`: *Grocerly Official, Suntory, Coca-Cola, Masan, Acecook,
  Vissan, CP, TH True Milk* — đều là **thương hiệu**, không phải merchant có tài khoản.
- [useradmin/forms.py:17](../grocerly/useradmin/forms.py#L17) cho nhân viên **chọn
  vendor bất kỳ** từ dropdown → vendor là thuộc tính sản phẩm, không phải chủ sở hữu.
- `useradmin` không lọc dữ liệu theo vendor: mọi staff thấy toàn bộ sản phẩm và doanh thu.
- `Vendor.user` chỉ được dùng làm giá trị dự phòng khi form không chọn vendor.

### Đề xuất

Thừa nhận đúng bản chất: Grocerly là **một siêu thị**, `Vendor` là **nhà cung cấp /
thương hiệu**. Đổi thuật ngữ trong báo cáo: "Người bán" → **"Nhân viên cửa hàng"**;
"Nhà cung cấp" giữ nghĩa thương hiệu.

### Hệ quả nếu chấp nhận

- Xóa được một mục nợ kỹ thuật: `useradmin` **không cần** giới hạn phạm vi theo vendor
  (vì không có khái niệm gian hàng riêng).
- Khớp với chính phần khảo sát của báo cáo — Grocerly được định vị cạnh Bách Hóa Xanh và
  Co.opmart (bán lẻ một chủ), không phải Shopee (sàn).
- Cần sửa mục 1.2.1, các use case của "Người bán", và Bảng 41 danh sách giao diện.

### Vì sao còn ở trạng thái Đề xuất

Thay đổi này chạm vào định vị đề tài, cần người thực hiện đồ án cân nhắc xem có ảnh
hưởng tới phần đã trao đổi với giảng viên hướng dẫn hay không.

---

## ADR-0004 — `AGENTS.md` là nguồn duy nhất cho chỉ dẫn AI

**Trạng thái:** Đã chốt · 2026-08-20

### Bối cảnh

Repo đã có `.github/copilot-instructions.md` viết từ giai đoạn đầu. Đến nay file này sai
gần như toàn bộ: nói dự án chỉ có 2 app (thực tế 4), SQLite là database mặc định (thực tế
PostgreSQL), *"chưa có requirements.txt"* (đã có từ lâu), và không hề nhắc tới DRF,
Gemini, VNPay, i18n hay soft delete.

Nay cần thêm chỉ dẫn cho Claude Code — nếu tạo thêm file độc lập nữa thì đến lượt nó
cũng sẽ lệch y hệt.

### Quyết định

- `AGENTS.md` (chuẩn mở, nhiều công cụ cùng đọc) chứa **toàn bộ** nội dung.
- `CLAUDE.md` import bằng cú pháp `@AGENTS.md`, chỉ giữ phần đặc thù Claude Code.
- `.github/copilot-instructions.md` rút gọn thành con trỏ về `AGENTS.md`.
- Thư mục `.claude/` (bộ công cụ ECC: skills, agents, commands) **được gitignore** — đó
  là công cụ cá nhân của lập trình viên, không phải mã nguồn dự án, và sẽ thêm ~780 file
  / 6.8 MB vào repo.

### Hệ quả

Sửa chỉ dẫn ở một chỗ duy nhất. Ba công cụ AI khác nhau đọc cùng một nội dung.
