# Nội dung cần sửa trong báo cáo

> ⚠️ **ĐANG VIẾT LẠI — 2026-08-25.** Thư mục này được soạn với giả định sai: rằng đang
> sửa bản **Tiểu luận chuyên ngành** trước khi bảo vệ. Thực tế tiểu luận **đã nộp và có
> điểm**; công việc hiện tại là **Khóa luận tốt nghiệp**, cùng đề tài, cùng GVHD.
>
> Ba chỗ đã biết là sai trong các file bên dưới:
>
> 1. **Bước 4.6 trong file 01 sai hoàn toàn.** Hình 4 **không có** use case "Duyệt sản phẩm" — chức
>    năng duyệt nằm gộp trong *"Quản lý toàn bộ sản phẩm"*. Không có gì để bỏ ở Hình 4.
> 2. **Generalization Quản trị viên ─▷ Người bán có vẻ ĐÃ CÓ** trong Hình 4. Cần xác nhận.
> 3. **Sót Hình 21** (Đăng bài đánh giá) — hình này cũng vẽ nhánh kiểm tra đã mua hàng.
>
> Ngoài ra mục **02** nay đã lỗi thời: [ADR-0006](../DECISIONS.md) đảo ngược ADR-0005,
> nên UC 3.2.14 và Hình 21 **giữ nguyên**, không sửa.
>
> Danh sách công việc đúng và đầy đủ nằm ở **[PLAN.md](../PLAN.md) giai đoạn 3 và 4**.
>
> ⚠️ **Cách đánh số bên trong các file 01–06 là của kế hoạch CŨ** (bước 4.1–4.7), không
> khớp với `PLAN.md` hiện tại. Khi đối chiếu phải theo `PLAN.md`, không theo số trong
> các file này.

Thư mục này chứa **nội dung soạn sẵn để copy-paste vào file Word**, tách theo từng nhóm
thay đổi.

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
| [04-chuong-4-test-case.md](04-chuong-4-test-case.md) | Bổ sung test case AI Chatbot + VNPay | [PLAN](../PLAN.md) 2.6 + 4.2 |
| [05-loi-trinh-bay.md](05-loi-trinh-bay.md) | Lỗi đánh số, lỗi câu chữ | [PLAN](../PLAN.md) 3.13–3.20, [SPEC-GAPS](../SPEC-GAPS.md) nhóm C |
| [06-huong-phat-trien.md](06-huong-phat-trien.md) | Các chức năng chưa cài → chuyển xuống Hướng phát triển | [SPEC-GAPS](../SPEC-GAPS.md) nhóm A |

## Thứ tự nên làm

1. **01** và **02** — hai mục này báo cáo đang mô tả chức năng **không còn tồn tại trong
   code**. Phản biện mở đúng hình là hỏi được ngay.
2. **06** — chuyển các chức năng chưa cài xuống Hướng phát triển. Cùng loại rủi ro.
3. **04** — bổ sung test case. Đây là phần *thêm điểm* chứ không phải vá lỗi.
4. **03** và **05** — chỉnh thuật ngữ và lỗi trình bày.
