# Khoảng cách giữa báo cáo và code

> Đối chiếu ngày 2026-08-20 với commit `42f6fdb`, cập nhật 2026-08-24.
> Nguồn: `CLC_CNPM_1_LEDUCPHAT.pdf` — *"Xây dựng website bán thực phẩm tích hợp trợ lý AI
> tự động đặt hàng"*, tiểu luận chuyên ngành CNPM, HCMUTE.

## Vì sao cần file này

Báo cáo đặc tả 26 use case và 43 sequence diagram. Một số mô tả **chức năng chưa được
cài đặt**. Với đồ án sắp bảo vệ, đây là rủi ro cụ thể: giảng viên phản biện chỉ cần mở
đúng sequence diagram và yêu cầu demo.

Với AI agent làm việc trong repo: **đừng tin báo cáo là mô tả code hiện tại.** Luôn `grep`
kiểm chứng trước khi khẳng định một chức năng tồn tại.

## A. Chức năng có trong báo cáo, không có trong code

| # | Báo cáo | Thực tế | Kiểm chứng |
|---|---|---|---|
| A1 | **Sửa & Xóa đánh giá** — UC 3.2.14, Hình 22–23 ghi rõ `core.views.ajax_edit_review`, `ajax_delete_review` | Không tồn tại. [core/urls.py](../grocerly/core/urls.py) chỉ có `ajax-add-review` | `grep -rn "edit_review\|delete_review"` → rỗng |
| A2 | Đánh giá yêu cầu **đã mua hàng (đơn Shipped)** — UC 3.2.14 Pre-Conditions | **Vẫn thiếu.** Ai đăng nhập cũng đánh giá được. (Điều kiện "mỗi user 1 lần" nay đã được kiểm ở server — [S-08](SECURITY.md#s-08--chốt-chặn-đánh-giá-chỉ-nằm-ở-template) — trước đó chỉ ẩn form ở template) | `ajax_add_review` |
| A3 | **Phân trang** — UC 3.2.3 Alternate Flow | Không có `Paginator` ở đâu | `grep -rn "Paginator\|paginate"` → rỗng |
| A4 | **"Làm sạch giỏ hàng"** — UC 3.2.6 Alternate Flow | Không có view/URL | `grep -rn "clear_cart"` → rỗng |
| A5 | ~~Cập nhật SL **vượt tồn kho → báo lỗi** — UC 3.2.6 Exception Flow~~ | ✅ **Đã đóng 2026-08-24** — `add_to_cart` và `update_cart` đều kiểm `stock_count`, trả `400` kèm số lượng còn lại | Sửa cùng [S-02](SECURITY.md#s-02--giả-mạo-giá-sản-phẩm) |
| A6 | Coupon có **ngày hết hạn** và **số lượt đã dùng** — UC 3.2.21 | Model `Coupon` chỉ có `code`, `discount`, `active` | [core/models.py](../grocerly/core/models.py) |
| A7 | **Hủy đơn (Cancel)** — UC 3.2.25 | `STATUS_CHOICES` chỉ có `processing`/`shipped`/`delivered` | [core/models.py:9](../grocerly/core/models.py#L9) |
| A8 | Không đổi được trạng thái khi đơn đã **Delivered** — UC 3.2.20 Exception Flow | `change_order_status` không kiểm tra gì | [useradmin/views.py](../grocerly/useradmin/views.py) |
| A9 | Cập nhật **mã vận đơn** ở dashboard nhân viên — UC 3.2.20 Alternate Flow | Field `tracking_id` có trong model nhưng `useradmin` không có giao diện nhập (chỉ sửa được qua Django Admin) | — |
| A10 | **Gửi email hàng loạt** cho người dùng — UC 3.2.22 Alternate Flow | Không có | — |
| A11 | **Quy trình duyệt sản phẩm** (`in_review`) — UC 3.2.19, Hình 28, Hình 40 | `add_product` đặt thẳng `'published'` | [useradmin/views.py:89](../grocerly/useradmin/views.py#L89) |

> A11 **sẽ được xử lý bằng cách sửa báo cáo, không sửa code** — xem
> [ADR-0002](DECISIONS.md). Các mục còn lại chờ quyết định.

## B. Code làm khác mô tả trong báo cáo

| # | Báo cáo | Thực tế |
|---|---|---|
| B1 | Nhân viên chỉ thấy dữ liệu **"thuộc gian hàng mình"** (mục 1.2.1) | `useradmin` trả `Product.objects.all()`, doanh thu toàn hệ thống. Chỉ `shop_page` lọc theo user |
| B2 | **Hình 26** — Nhờ AI thêm vào giỏ: server gọi hàm và tự ghi Django Session | Server trả cờ `action: confirm_add_cart`; **JS phía client** mới gọi `/add-to-cart/`. Đây là thiết kế **có chủ ý** (giữ vòng xác nhận của người dùng) — nên sửa sơ đồ theo code, xem [ARCHITECTURE.md](ARCHITECTURE.md) mục 4.3 |
| B3 | **Hình 30** — Xóa sản phẩm: có nhánh kiểm tra đơn hàng liên quan rồi mới xóa mềm/cứng | `delete_product` gọi thẳng `product.delete()` — mà `SoftDeleteModel` không override `delete()` ở tầng instance nên **xóa cứng vô điều kiện** |
| B4 | **ERD (Hình 45)** — `core_product.tags` là cột `VARCHAR` | `django-taggit` lưu ở bảng riêng (`taggit_tag`, `taggit_taggeditem`). ERD cũng thiếu bảng nối M2M `cartorder ↔ coupon` |
| B5 | **Bảng 28** mô tả `core_tag` như một bảng thật | `core.models.Tag` là `class Tag(models.Model): pass` — model rỗng không dùng |
| B6 | Định vị **multi-vendor**, "Người bán" có gian hàng riêng | `Vendor` thực chất là thương hiệu/nhà cung cấp — xem [ADR-0003](DECISIONS.md) |

## C. Lỗi trình bày trong báo cáo

| # | Vị trí | Vấn đề |
|---|---|---|
| C1 | tr.54 và tr.67 | **Trùng số mục**: hai mục cùng đánh `3.5` (Thiết kế CSDL và Thiết kế giao diện). Mục sau phải là `3.6`, kéo theo `3.6.1`/`3.6.2` |
| C2 | tr.92 | Caption ghi *"Hình 3.5.23"* thay vì "Hình 72"; hình này **thiếu hẳn** trong Danh mục hình ảnh (nhảy từ Hình 71 tr.91 sang Hình 72 tr.93) |
| C3 | tr.6 | Câu lỗi logic: *"Shopee là một phân nhánh chiến lược của nền tảng thương mại điện tử khổng lồ Shopee"* |
| C4 | tr.3 vs tr.33 | Tên Chương 2 không khớp đề cương: *"…và quy trình phát triển hệ thống"* vs *"…và cơ sở lý thuyết"* |
| C5 | tr.1 | Lời cảm ơn ký **"Nhóm sinh viên"** nhưng đây là đồ án cá nhân |
| C6 | Chương 2 | Thiếu **Django REST Framework** (nền tảng của `/api/v1/` phục vụ chatbot), i18n/gettext, WhiteNoise, django-taggit |
| C7 | Chương 4 | Chỉ có **5 test case**, **không TC nào cho AI Chatbot và VNPay** — đúng hai điểm nhấn của đề tài |
| C8 | tr.108 | In nguyên **mật khẩu 3 tài khoản production đang chạy thật**. Cần đổi sau khi bảo vệ (repo public + site live) |

## Cách dùng file này

1. **Trước khi sửa code**: kiểm tra thay đổi có chạm vào mục nào ở đây không.
2. **Sau khi sửa code**: cập nhật dòng tương ứng, hoặc xóa nếu khoảng cách đã đóng.
3. **Trước khi bảo vệ**: mục nào còn ở nhóm A là câu hỏi có thể bị hỏi — hoặc cài cho
   xong, hoặc chuyển xuống phần *"Hướng phát triển"* của báo cáo.
