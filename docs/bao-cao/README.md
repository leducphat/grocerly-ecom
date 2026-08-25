# Nội dung cần sửa trong báo cáo

Thư mục này chứa **nội dung soạn sẵn để copy-paste vào file Word**, tách theo từng nhóm
thay đổi. Đây là phần "Giai đoạn 4" của [PLAN.md](../PLAN.md) cộng các mục F, G, H của
backlog và nhóm C trong [SPEC-GAPS.md](../SPEC-GAPS.md).

## ⚠️ Đọc trước khi dùng

**File báo cáo không nằm trong repo** (`CLC_CNPM_1_LEDUCPHAT.pdf` ở máy cá nhân). Nội
dung dưới đây được soạn dựa trên những gì đã ghi lại trong `docs/`, **không phải** dựa
trên việc đọc lại bản gốc. Hệ quả:

- Chỗ nào ghi **"Bỏ"** là dựa vào mô tả trong SPEC-GAPS — cần bạn mở đúng trang xác nhận
  câu chữ trước khi xóa.
- Chỗ nào ghi **"Thay bằng"** là **đề xuất mới**, viết theo văn phong báo cáo. Bạn sửa
  lại cho khớp giọng văn của mình.
- Số trang / số hình lấy từ bản đối chiếu ngày 2026-08-20. Nếu bạn đã sửa file từ đó tới
  giờ thì số thứ tự có thể lệch.

Phần trong khối ```` ``` ```` là nội dung để copy. Phần ngoài là chỉ dẫn cho bạn.

## Các file

| File | Nội dung | Nguồn |
|---|---|---|
| [01-bo-luong-duyet-san-pham.md](01-bo-luong-duyet-san-pham.md) | Bỏ quy trình duyệt sản phẩm khỏi báo cáo | [ADR-0002](../DECISIONS.md) |
| [02-danh-gia-san-pham.md](02-danh-gia-san-pham.md) | Sửa/xóa đánh giá đã cài; bỏ điều kiện "đã mua" | [ADR-0005](../DECISIONS.md) |
| [03-tac-nhan-va-thuat-ngu.md](03-tac-nhan-va-thuat-ngu.md) | Generalization tác nhân; "Người bán" → "Nhân viên" | [ADR-0001](../DECISIONS.md), [ADR-0003](../DECISIONS.md) |
| [04-chuong-4-test-case.md](04-chuong-4-test-case.md) | Bổ sung test case AI Chatbot + VNPay | backlog G |
| [05-loi-trinh-bay.md](05-loi-trinh-bay.md) | Lỗi đánh số, lỗi câu chữ | backlog H, [SPEC-GAPS](../SPEC-GAPS.md) nhóm C |
| [06-huong-phat-trien.md](06-huong-phat-trien.md) | Các chức năng chưa cài → chuyển xuống Hướng phát triển | [SPEC-GAPS](../SPEC-GAPS.md) nhóm A |

## Thứ tự nên làm

1. **01** và **02** — hai mục này báo cáo đang mô tả chức năng **không còn tồn tại trong
   code**. Phản biện mở đúng hình là hỏi được ngay.
2. **06** — chuyển các chức năng chưa cài xuống Hướng phát triển. Cùng loại rủi ro.
3. **04** — bổ sung test case. Đây là phần *thêm điểm* chứ không phải vá lỗi.
4. **03** và **05** — chỉnh thuật ngữ và lỗi trình bày.
