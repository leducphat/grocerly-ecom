# 06 — Chuyển chức năng chưa cài xuống Hướng phát triển

> ⛔ **PHẦN LỚN FILE NÀY ĐÃ HẾT HIỆU LỰC — 2026-08-26. Đừng dán vào Word.**
>
> File được soạn cho lựa chọn *"sửa báo cáo để né gap"*. **KLTN đã đảo ngược nguyên tắc
> đó** (xem [PLAN.md](../PLAN.md) mục *Nguyên tắc đã đảo chiều*): với phần lớn khoảng
> cách, nay **viết code để đóng gap** tốt hơn.
>
> Tính tới 2026-08-26, nhóm A chỉ còn **A10** và **A11** là còn mở. Chín mục còn lại đã
> được cài xong bằng code. Cụ thể, đoạn soạn sẵn cho **A6** ở dưới bảo *bỏ mô tả ngày hết
> hạn và số lượt* — mà bước 2.9 vừa **cài đúng hai thuộc tính đó**. Dán đoạn đó vào báo
> cáo là tự tạo một gap mới, ngược chiều.
>
> **Còn dùng được:** mục A11 (ADR-0002 giữ nguyên quyết định không cài luồng duyệt) và
> mục A10 (email hàng loạt, [PLAN](../PLAN.md) bước 2.13 chưa làm).
>
> Bảng trạng thái bên dưới **đã được cập nhật** theo [SPEC-GAPS.md](../SPEC-GAPS.md);
> phần văn bản soạn sẵn thì giữ nguyên văn để đối chiếu, **không phải để dùng lại**.

Đây là nhóm **A** trong [SPEC-GAPS.md](../SPEC-GAPS.md): những chức năng **báo cáo có mô
tả nhưng code không có**. Mỗi mục còn sót là một câu hỏi phản biện có thể bị hỏi — giảng
viên chỉ cần mở đúng use case và yêu cầu demo.

Với mỗi mục có hai lựa chọn: **cài cho xong**, hoặc **sửa báo cáo** để không hứa thứ chưa
có. File này soạn cho lựa chọn thứ hai.

## Tình trạng từng mục

| # | Chức năng | Vị trí trong báo cáo | Trạng thái |
|---|---|---|---|
| A1 | Sửa & Xóa đánh giá | UC 3.2.14, Hình 22–23 | ✅ **Đã cài** — giữ nguyên báo cáo |
| A5 | Vượt tồn kho báo lỗi | UC 3.2.6 Exception Flow | ✅ **Đã cài** — giữ nguyên báo cáo |
| A11 | Quy trình duyệt sản phẩm | UC 3.2.19, Hình 28, 40 | ⛔ Bỏ khỏi code — xem [01](01-bo-luong-duyet-san-pham.md) |
| A2 | Đánh giá yêu cầu đã mua hàng | UC 3.2.14 Pre-Conditions | ✅ **Đã cài 2026-08-26** (bước 2.12) — giữ nguyên báo cáo |
| A3 | Phân trang | UC 3.2.3 Alternate Flow | ✅ **Đã cài 2026-08-26** (bước 2.8) — giữ nguyên báo cáo |
| A4 | Làm sạch giỏ hàng | UC 3.2.6 Alternate Flow | ✅ **Đã cài 2026-08-26** (bước 2.3) — giữ nguyên báo cáo |
| A6 | Coupon có hạn dùng và số lượt | UC 3.2.21 | ✅ **Đã cài 2026-08-26** (bước 2.9) — ⛔ **đoạn soạn sẵn bên dưới phải BỎ** |
| A7 | Hủy đơn hàng | UC 3.2.25 | ✅ **Đã cài 2026-08-26** (bước 2.10) — bổ sung hai tiền điều kiện, xem [ADR-0007](../DECISIONS.md) |
| A8 | Chặn đổi trạng thái khi đã giao | UC 3.2.20 Exception Flow | ✅ **Đã cài 2026-08-26** (bước 2.2) — giữ nguyên báo cáo |
| A9 | Nhập mã vận đơn ở trang nhân viên | UC 3.2.20 Alternate Flow | ✅ **Đã cài 2026-08-26** (bước 2.7) — giữ nguyên báo cáo |
| A10 | Gửi email hàng loạt | UC 3.2.22 Alternate Flow | ❌ Chưa cài |

**Chỉ còn A10 và A11 là còn mở.** Mọi mục khác đã được cài bằng code, báo cáo đang đúng
— đừng chuyển bất kỳ mục nào trong số đó xuống Hướng phát triển.

---

## Cách 1 — Sửa trực tiếp trong use case

⚠️ **Chỉ còn áp dụng cho A10.** A3, A4 và A8 đều đã được cài — xóa luồng phụ của chúng
khỏi use case là làm báo cáo mất mô tả cho code đang chạy.

~~Với các mục nằm ở Alternate/Exception Flow (A3, A4, A8, A10), cách gọn nhất là **xóa
luồng phụ đó** khỏi use case tương ứng.~~

Với A6 và A7 thì phải sửa cả phần mô tả thuộc tính và trạng thái:

⛔ ~~**A6 — UC 3.2.21 (Quản lý mã giảm giá):** bỏ mô tả về ngày hết hạn và số lượt đã dùng.~~
**HẾT HIỆU LỰC 2026-08-26** — bước 2.9 đã cài `valid_to`, `used_count` và `usage_limit`.
Giữ nguyên mô tả trong báo cáo, và **bổ sung** `usage_limit` vào ERD Hình 45 cùng bảng mô
tả `core_coupon` ([PLAN](../PLAN.md) bước 3.23–3.24).

```
Mã giảm giá gồm ba thuộc tính: mã code do quản trị viên đặt, phần trăm giảm
giá, và cờ kích hoạt cho phép bật hoặc tắt mã mà không cần xóa. Mã đang tắt sẽ
bị từ chối khi khách áp dụng ở bước thanh toán.
```

⛔ ~~**A7 — UC 3.2.25 (Hủy đơn):** bỏ hẳn use case này…~~ **HẾT HIỆU LỰC 2026-08-26** —
bước 2.10 đã cài trạng thái `cancelled`, và đơn hàng nay có **bốn** trạng thái chứ không
phải ba như đoạn dưới viết. Xem [ADR-0007](../DECISIONS.md); việc phải làm với báo cáo là
[PLAN](../PLAN.md) bước 3.21–3.22. Đoạn dưới giữ nguyên văn để đối chiếu:

```
Đơn hàng có ba trạng thái xử lý: Đang xử lý (processing), Đã giao cho đơn vị
vận chuyển (shipped) và Đã giao hàng (delivered). Nhân viên cập nhật trạng thái
này từ trang quản trị. Khi chuyển sang trạng thái Đã giao cho đơn vị vận
chuyển, hệ thống tự động trừ số lượng tồn kho tương ứng.
```

⛔ ~~**A9 — UC 3.2.20:** …chưa có ô nhập ở giao diện nhân viên.~~ **HẾT HIỆU LỰC
2026-08-26** — bước 2.7 đã thêm ô nhập ở trang chi tiết đơn của nhân viên, và mã hiện
luôn ở trang đơn hàng của khách. Báo cáo giữ nguyên.

---

## Cách 2 — Đoạn văn cho mục Hướng phát triển

Dùng nếu bạn muốn giữ các chức năng này như định hướng tương lai thay vì xóa hẳn:

```
Hướng phát triển

Trong phạm vi tiểu luận, hệ thống tập trung hoàn thiện luồng nghiệp vụ cốt lõi:
duyệt sản phẩm, giỏ hàng, thanh toán qua VNPay và trợ lý AI tư vấn. Một số chức
năng bổ trợ được xác định nhưng chưa triển khai, dự kiến bổ sung ở giai đoạn
tiếp theo:

Về trải nghiệm mua hàng: phân trang danh sách sản phẩm để giảm thời gian tải
khi số lượng sản phẩm tăng; chức năng xóa toàn bộ giỏ hàng trong một thao tác;
và chức năng hủy đơn hàng cho khách trong khoảng thời gian đơn còn ở trạng thái
Đang xử lý.

Về quản trị: mở rộng mã giảm giá với thời hạn hiệu lực và giới hạn số lượt sử
dụng; bổ sung ô nhập mã vận đơn ngay trên trang quản trị của nhân viên thay vì
phải thao tác qua trang quản trị hệ thống; ràng buộc không cho thay đổi trạng
thái của đơn hàng đã giao thành công; và chức năng gửi thông báo hàng loạt qua
thư điện tử tới nhóm khách hàng.

Về mô hình dữ liệu: bổ sung khóa ngoại từ dòng chi tiết đơn hàng tới sản phẩm,
song song với bản sao tĩnh phục vụ hóa đơn. Thay đổi này là điều kiện tiên
quyết để cài đặt ràng buộc chỉ khách đã mua hàng mới được đánh giá sản phẩm,
đồng thời khắc phục sai sót trừ tồn kho khi hai sản phẩm trùng tên.

Về vận hành: bổ sung giới hạn tổng số lượt gọi trợ lý AI theo ngày trên toàn hệ
thống, bên cạnh giới hạn theo từng người dùng đã có, nhằm bảo vệ hạn ngạch dịch
vụ trước truy cập bất thường từ nhiều nguồn.
```

---

## Nếu còn thời gian: hai mục nên cài thay vì chuyển xuống

Không phải mục nào cũng đáng bỏ. Hai mục này rẻ và đóng được khoảng cách thật:

| Mục | Vì sao rẻ |
|---|---|
| **A8** — chặn đổi trạng thái khi đơn đã giao | Thêm vài dòng kiểm tra vào `change_order_status`. Không migration, không đụng giao diện |
| **A4** — làm sạch giỏ hàng | Một view xóa `cart_data_obj` khỏi session, một nút, một dòng URL |

A3 (phân trang) cũng không khó nhưng chạm vào nhiều trang danh sách nên rủi ro cao hơn ở
giai đoạn sắp bảo vệ.
