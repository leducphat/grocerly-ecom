# Khoảng cách giữa báo cáo và code

> Đối chiếu ngày 2026-08-20, cập nhật 2026-08-25 sau khi **đọc trực tiếp bản gốc**.
> Nguồn: `CLC_CNPM_1_LEDUCPHAT.pdf` — *"Xây dựng website bán thực phẩm tích hợp trợ lý AI
> tự động đặt hàng"*, tiểu luận chuyên ngành CNPM, HCMUTE.
>
> ⚠️ **Tiểu luận đã nộp và có điểm.** File này giờ phục vụ **Khóa luận tốt nghiệp** —
> cùng đề tài, cùng GVHD. Xem [PLAN.md](PLAN.md).
>
> Cập nhật 2026-08-26: đóng **A2**, **A8** và **B3**; **B11** xong phần code, chờ deploy.

> **Ghi chú A2 — "Shipped" hiểu theo nghĩa nào.** UC 3.2.14 viết điều kiện là đơn
> *Shipped*. Code nhận **cả `shipped` lẫn `delivered`**, vì `delivered` nằm sau `shipped`
> trong vòng đời đơn: hiểu chữ đó theo nghĩa hẹp thì khách nhận được hàng rồi lại *mất*
> quyền đánh giá. `processing` không được tính — đơn còn có thể bị hủy trước khi rời kho.
> Đây là chỗ code **rộng hơn** báo cáo một cách có chủ ý, không phải lệch.

## Vì sao cần file này

Báo cáo đặc tả **26 use case** (Bảng 1–26) và **39 lược đồ tuần tự** (Hình 5–43),
tổng cộng 75 hình và 75 bảng. Một số mô tả **chức năng chưa được
cài đặt**. Với đồ án sắp bảo vệ, đây là rủi ro cụ thể: giảng viên phản biện chỉ cần mở
đúng sequence diagram và yêu cầu demo.

Với AI agent làm việc trong repo: **đừng tin báo cáo là mô tả code hiện tại.** Luôn `grep`
kiểm chứng trước khi khẳng định một chức năng tồn tại.

## A. Chức năng có trong báo cáo, không có trong code

| # | Báo cáo | Thực tế | Kiểm chứng |
|---|---|---|---|
| A1 | ~~**Sửa & Xóa đánh giá** — UC 3.2.14, Hình 22–23~~ | ✅ **Đã đóng 2026-08-25** — `ajax_edit_review` và `ajax_delete_review` đúng tên báo cáo ghi, kèm nút Sửa/Xóa ở trang chi tiết. Chỉ chủ đánh giá đụng được; của người khác trả 404 | `EditDeleteReviewTests` |
| A2 | ~~Đánh giá yêu cầu **đã mua hàng (đơn Shipped)** — UC 3.2.14 Pre-Conditions **và Hình 21**~~ | ✅ **Đã đóng 2026-08-26** — `has_purchased` tra theo khóa ngoại mới của `CartOrderItem` ([ADR-0006](DECISIONS.md), bước 2.11). Chưa mua mà POST thẳng vào endpoint thì `403`; trang chi tiết ẩn form **kèm lý do**. Nhận cả `shipped` lẫn `delivered` — xem ghi chú dưới bảng. **Báo cáo giữ nguyên**, không phải sửa chữ nào | `core/test_review_purchase.py` |
| A3 | **Phân trang** — UC 3.2.3 Alternate Flow | Không có `Paginator` ở đâu | `grep -rn "Paginator\|paginate"` → rỗng |
| A4 | ~~**"Làm sạch giỏ hàng"** — UC 3.2.6 Alternate Flow~~ | ✅ **Đã đóng 2026-08-26** — `clear_cart` (POST + CSRF), nút ở trang giỏ hàng. Đừng nhầm với `delete_item_from_cart` (xóa **một** sản phẩm) vốn đã có sẵn từ trước và vẫn chạy đúng | `ClearCartTests` |
| A5 | ~~Cập nhật SL **vượt tồn kho → báo lỗi** — UC 3.2.6 Exception Flow~~ | ✅ **Đã đóng 2026-08-24** — `add_to_cart` và `update_cart` đều kiểm `stock_count`, trả `400` kèm số lượng còn lại | Sửa cùng [S-02](SECURITY.md#s-02--giả-mạo-giá-sản-phẩm) |
| A6 | Coupon có **ngày hết hạn** và **số lượt đã dùng** — UC 3.2.21 | Model `Coupon` chỉ có `code`, `discount`, `active` | [core/models.py](../grocerly/core/models.py) |
| A7 | **Hủy đơn (Cancel)** — UC 3.2.25 | `STATUS_CHOICES` chỉ có `processing`/`shipped`/`delivered` | [core/models.py:9](../grocerly/core/models.py#L9) |
| A8 | ~~Không đổi được trạng thái khi đơn đã **Delivered** — UC 3.2.20 Exception Flow~~ | ✅ **Đã đóng 2026-08-26** — chặn ở view và khóa luôn form. Kèm theo: `change_order_status` trước đây nhận **mọi chuỗi** từ POST, mà option đầu của dropdown lại gửi `value="pending"` — giá trị không có trong `STATUS_CHOICES`. Nay option dựng từ model và view lọc qua whitelist | `ChangeOrderStatusTests` |
| A9 | Cập nhật **mã vận đơn** ở dashboard nhân viên — UC 3.2.20 Alternate Flow | Field `tracking_id` có trong model nhưng `useradmin` không có giao diện nhập (chỉ sửa được qua Django Admin) | — |
| A10 | **Gửi email hàng loạt** cho người dùng — UC 3.2.22 Alternate Flow | Không có | — |
| A11 | **Quy trình duyệt sản phẩm** (`in_review`) — UC 3.2.19, Hình 28, Hình 40 | ⚠️ **Khoảng cách nay rộng hơn, có chủ ý.** `in_review`/`rejected` đã bị **xóa khỏi code** (2026-08-24); nhân viên tự bấm "Lưu nháp" / "Đăng bán" | [ADR-0002](DECISIONS.md) |

> A11 được xử lý bằng cách **sửa báo cáo cho khớp code**, không cài luồng duyệt — xem
> [ADR-0002](DECISIONS.md). Phần code đã xong; phần báo cáo là
> [PLAN.md](PLAN.md) bước 3.3 (UC 3.2.19, UC 3.2.24, Hình 28, Hình 29, bỏ Hình 40,
> Bảng 30) — **chưa làm**. Lưu ý: Hình 4 **không** có use case "Duyệt sản phẩm" nên
> không phải sửa ở đó. Các mục còn lại chờ quyết định.

## B. Code làm khác mô tả trong báo cáo

| # | Báo cáo | Thực tế |
|---|---|---|
| B1 | Nhân viên chỉ thấy dữ liệu **"thuộc gian hàng mình"** (mục 1.2.1) | `useradmin` trả `Product.objects.all()`, doanh thu toàn hệ thống. Chỉ `shop_page` lọc theo user |
| B2 | **Hình 26** — Nhờ AI thêm vào giỏ: server gọi hàm và tự ghi Django Session | Server trả cờ `action: confirm_add_cart`; **JS phía client** mới gọi `/add-to-cart/`. Đây là thiết kế **có chủ ý** (giữ vòng xác nhận của người dùng) — nên sửa sơ đồ theo code, xem [ARCHITECTURE.md](ARCHITECTURE.md) mục 4.3 |
| B3 | ~~**Hình 30** — Xóa sản phẩm: có nhánh kiểm tra đơn hàng liên quan rồi mới xóa mềm/cứng~~ | ✅ **Đã đóng 2026-08-26** — code nay khớp hình. Sản phẩm đã có đơn thì xóa mềm, chưa có đơn thì xóa cứng. Việc dò "đã có đơn chưa" nay tra theo **khóa ngoại** (bước 2.11); riêng dòng hóa đơn cũ chưa có khóa ngoại thì vẫn so tên, cố ý — xem `product_has_order_history` |
| B4 | **ERD (Hình 45)** — `core_product.tags` là cột `VARCHAR` | `django-taggit` lưu ở bảng riêng (`taggit_tag`, `taggit_taggeditem`). ERD cũng thiếu bảng nối M2M `cartorder ↔ coupon` |
| B5 | **Bảng 28** mô tả `core_tag` như một bảng thật | `core.models.Tag` là `class Tag(models.Model): pass` — model rỗng không dùng |
| B6 | Định vị **multi-vendor**, "Người bán" có gian hàng riêng | `Vendor` thực chất là thương hiệu/nhà cung cấp. [ADR-0003](DECISIONS.md) **đã chốt 2026-08-25** → sửa báo cáo, xem [PLAN](PLAN.md) bước 3.9–3.11 |
| B7 | **Hình 10** (Thêm vào giỏ) vẽ 4 lifeline, **không có Product Model / Database**; ghi *"Cộng thêm số lượng"* và dùng POST | Sau [S-02](SECURITY.md), `add_to_cart` **bắt buộc** truy vấn database để lấy giá; code **ghi đè** số lượng và dùng GET |
| B8 | **Hình 11** (Cập nhật giỏ) có nhánh `[Số lượng mới = 0] Xóa sản phẩm khỏi Session` | Code ép tối thiểu là 1, không xóa; và nay có thêm bước kiểm tồn kho mà hình chưa vẽ |
| B9 | **Không có lược đồ tuần tự nào cho `vnpay_ipn`** | IPN là chỗ kiểm chữ ký, kiểm số tiền và chống xác nhận trùng — phần đáng trình bày nhất của tích hợp VNPay lại không có hình |
| B10 | **Bảng 30** mô tả `product_status` là *"Trạng thái xử lý"* | Giống hệt mô tả ở Bảng 32 và 33 dù nghĩa hoàn toàn khác (đăng bán vs giao hàng) — báo cáo đang che mất bẫy #1 |
| B11 | **ERD Hình 45 và Bảng 32 không có `cartorder.stripe_payment_intent`** | 🔸 **Code đã xong 2026-08-26**, chờ deploy. Migration `0006_drop_stripe_payment_intent` đã viết và đã áp lên SQLite local; cột **vẫn còn trên production Neon** cho tới khi merge vào `main`. Ở mục này báo cáo đúng còn code sai, nên không phải sửa báo cáo |

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
