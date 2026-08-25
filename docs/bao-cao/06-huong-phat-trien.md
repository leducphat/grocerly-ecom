# 06 — Chuyển chức năng chưa cài xuống Hướng phát triển

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
| A2 | Đánh giá yêu cầu đã mua hàng | UC 3.2.14 Pre-Conditions | ⛔ Không cài — xem [02](02-danh-gia-san-pham.md) |
| A3 | Phân trang | UC 3.2.3 Alternate Flow | ❌ Chưa cài |
| A4 | Làm sạch giỏ hàng | UC 3.2.6 Alternate Flow | ❌ Chưa cài |
| A6 | Coupon có hạn dùng và số lượt | UC 3.2.21 | ❌ Chưa cài |
| A7 | Hủy đơn hàng | UC 3.2.25 | ❌ Chưa cài |
| A8 | Chặn đổi trạng thái khi đã giao | UC 3.2.20 Exception Flow | ❌ Chưa cài |
| A9 | Nhập mã vận đơn ở trang nhân viên | UC 3.2.20 Alternate Flow | ⚠️ Có trường trong CSDL, thiếu giao diện |
| A10 | Gửi email hàng loạt | UC 3.2.22 Alternate Flow | ❌ Chưa cài |

**A1 và A5 đã được cài trong đợt sửa 2026-08-24/25** — hai mục này báo cáo đang đúng,
đừng chuyển xuống Hướng phát triển.

---

## Cách 1 — Sửa trực tiếp trong use case

Với các mục nằm ở Alternate/Exception Flow (A3, A4, A8, A10), cách gọn nhất là **xóa
luồng phụ đó** khỏi use case tương ứng. Luồng chính vẫn đúng, use case vẫn demo được.

Với A6 và A7 thì phải sửa cả phần mô tả thuộc tính và trạng thái:

**A6 — UC 3.2.21 (Quản lý mã giảm giá):** bỏ mô tả về ngày hết hạn và số lượt đã dùng.

```
Mã giảm giá gồm ba thuộc tính: mã code do quản trị viên đặt, phần trăm giảm
giá, và cờ kích hoạt cho phép bật hoặc tắt mã mà không cần xóa. Mã đang tắt sẽ
bị từ chối khi khách áp dụng ở bước thanh toán.
```

**A7 — UC 3.2.25 (Hủy đơn):** bỏ hẳn use case này, hoặc mô tả lại đúng những gì hệ thống
làm được. Trạng thái đơn hàng hiện chỉ có ba giá trị:

```
Đơn hàng có ba trạng thái xử lý: Đang xử lý (processing), Đã giao cho đơn vị
vận chuyển (shipped) và Đã giao hàng (delivered). Nhân viên cập nhật trạng thái
này từ trang quản trị. Khi chuyển sang trạng thái Đã giao cho đơn vị vận
chuyển, hệ thống tự động trừ số lượng tồn kho tương ứng.
```

**A9 — UC 3.2.20:** sửa cho đúng thực tế — trường mã vận đơn có tồn tại trong cơ sở dữ
liệu nhưng chỉ sửa được qua trang quản trị Django, chưa có ô nhập ở giao diện nhân viên.

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
