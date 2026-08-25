# 02 — Đánh giá sản phẩm (UC 3.2.14)

Use case này có **hai vế đi ngược chiều nhau**, đừng sửa gộp:

| Vế | Việc |
|---|---|
| **Sửa & Xóa đánh giá** (Hình 22–23) | ✅ **Đã cài xong** 2026-08-25 — báo cáo đang **đúng**, giữ nguyên |
| **Pre-Condition "đã mua hàng (đơn Shipped)"** | ⛔ **Cố ý không cài** — [ADR-0005](../DECISIONS.md), phải bỏ khỏi Pre-Conditions |

---

## Vế 1 — Sửa & Xóa đánh giá: giữ nguyên, không phải sửa gì

Trước 2026-08-25 đây là khoảng cách A1 trong SPEC-GAPS: báo cáo ghi đích danh
`core.views.ajax_edit_review` và `ajax_delete_review` ở Hình 22–23 nhưng code không có.
**Nay đã cài đúng hai tên đó**, nên báo cáo khớp code.

Nếu muốn mô tả thêm cho đầy đủ, có thể bổ sung vào Business Rules:

```
- Chỉ chính tác giả của đánh giá mới sửa hoặc xóa được đánh giá đó. Thao tác
  trên đánh giá của người khác bị hệ thống từ chối và trả về mã lỗi 404, không
  phân biệt với trường hợp đánh giá không tồn tại.
- Sau khi xóa đánh giá, khách hàng được viết đánh giá mới cho sản phẩm đó.
```

---

## Vế 2 — Bỏ Pre-Condition "đã mua hàng"

**Bỏ:** dòng Pre-Conditions yêu cầu khách hàng phải **đã mua sản phẩm (đơn ở trạng thái
Shipped)** mới được đánh giá.

**Thay bằng:**

```
Pre-Conditions:
- Khách hàng đã đăng nhập vào hệ thống.
- Khách hàng chưa từng đánh giá sản phẩm này. Mỗi tài khoản chỉ được viết một
  đánh giá cho mỗi sản phẩm; điều kiện này được kiểm tra ở phía máy chủ.
```

### Lý do — đưa vào mục Hướng phát triển

Đây là lý do kỹ thuật thật, nên nói thẳng thay vì lờ đi. Phản biện hỏi *"sao ai cũng
đánh giá được?"* thì đây là câu trả lời:

```
Điều kiện "phải mua hàng rồi mới được đánh giá" chưa được cài đặt vì hạn chế
của mô hình dữ liệu hiện tại. Bảng core_cartorderitem lưu thông tin sản phẩm
đã mua dưới dạng bản sao tĩnh (tên, ảnh, giá tại thời điểm đặt hàng) và không
giữ khóa ngoại tới bảng core_product. Thiết kế này có chủ đích: hóa đơn của
khách không thay đổi khi sản phẩm bị sửa thông tin hoặc bị gỡ khỏi cửa hàng.

Hệ quả là hệ thống không truy ngược được từ một dòng đơn hàng về đúng sản phẩm
gốc, mà chỉ có thể đối chiếu theo tên. Cách đối chiếu này sai trong hai tình
huống có thật: khi nhân viên đổi tên sản phẩm sau khi đã bán, người mua thật sẽ
mất quyền đánh giá; và khi hai sản phẩm trùng tên, khách mua sản phẩm này lại
đánh giá được sản phẩm kia. Việc chặn nhầm người dùng hợp lệ mà không nêu được
lý do gây thiệt hại lớn hơn so với việc chưa có điều kiện này.

Hướng phát triển: bổ sung khóa ngoại tới sản phẩm cho bảng core_cartorderitem,
đồng thời vẫn giữ bản sao tĩnh phục vụ hóa đơn. Khi đó điều kiện "đã mua hàng"
mới kiểm tra được chính xác, và cũng khắc phục luôn lỗi trừ nhầm tồn kho khi
hai sản phẩm trùng tên ở chức năng cập nhật trạng thái đơn hàng.
```

> Đoạn cuối là một điểm cộng chứ không phải điểm trừ: nó cho thấy bạn **biết** giới hạn
> của thiết kế và **biết** cách khắc phục, thay vì bỏ sót.
