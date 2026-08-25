# 03 — Tác nhân và thuật ngữ

Gộp hai việc vì cùng đụng vào Hình 4 và chương 1: mục **F** của backlog —
[ADR-0001](../DECISIONS.md) và [ADR-0003](../DECISIONS.md).

---

## Phần A — Generalization giữa Quản trị viên và Nhân viên (ADR-0001)

**Vấn đề:** Hình 4 đã dùng generalization đúng cho cặp *Khách hàng ─▷ Khách vãng lai*,
nhưng **thiếu** cặp *Quản trị viên ─▷ Nhân viên*. Trong code, `admin_required` chấp nhận
cả `is_superuser` lẫn `is_staff` — tức Quản trị viên **kế thừa toàn bộ** quyền của Nhân
viên. Không vẽ generalization thì phải nhân đôi use case cho hai tác nhân, vừa rối vừa sai
nguyên tắc mô hình hóa.

**Việc cần làm ở Hình 4:** thêm mũi tên generalization từ **Quản trị viên** tới **Nhân
viên**, rồi **bỏ** các use case bị vẽ trùng cho cả hai tác nhân (quản lý sản phẩm, tồn
kho, đơn hàng) — chỉ nối chúng vào Nhân viên.

**Nội dung mô tả kèm theo:**

```
Quản trị viên kế thừa toàn bộ chức năng của Nhân viên, do đó trong sơ đồ Use
Case hai tác nhân này có quan hệ tổng quát hóa (generalization). Ranh giới giữa
hai vai trò nằm ở phạm vi thẩm quyền chứ không ở khả năng kỹ thuật:

- Nhân viên: quản lý sản phẩm, tồn kho, đơn hàng.
- Quản trị viên: kế thừa các quyền trên, đồng thời quản lý tài khoản người
  dùng và phân quyền, quản lý danh mục dùng chung, quản lý mã giảm giá, gỡ sản
  phẩm vi phạm và xem toàn bộ doanh thu hệ thống.

Việc tách hai vai trò dựa trên nguyên tắc đặc quyền tối thiểu: nhân viên trực
ca không cần và không nên có khả năng xóa tài khoản hay thay đổi cấu hình thanh
toán, nhằm giảm thiệt hại nếu tài khoản bị lộ. Cách phân chia này tương ứng với
vai trò Shop Manager của WooCommerce và Staff account của Shopify.
```

---

## Phần B — "Người bán" → "Nhân viên cửa hàng" (ADR-0003)

> ⚠️ **ADR-0003 đang ở trạng thái *Đề xuất*, chưa chốt.** Thay đổi này chạm vào định vị
> đề tài. Cân nhắc xem có ảnh hưởng tới nội dung đã trao đổi với giảng viên hướng dẫn
> không rồi hãy làm.

**Vấn đề:** Báo cáo định vị Grocerly là hệ thống **multi-vendor**, "Người bán
(Vendor/Nhân viên cửa hàng)" đăng nhập vận hành gian hàng riêng. Thực tế trong code:

- Dữ liệu bảng `core_vendor` là *Grocerly Official, Suntory, Coca-Cola, Masan, Acecook,
  Vissan, CP, TH True Milk* — đều là **thương hiệu**, không phải người bán có tài khoản.
- Nhân viên chọn Vendor bất kỳ từ danh sách khi đăng sản phẩm → Vendor là **thuộc tính
  của sản phẩm**, không phải chủ sở hữu.
- Trang quản trị **không** giới hạn dữ liệu theo vendor: mọi nhân viên thấy toàn bộ sản
  phẩm và doanh thu.

**Chỗ cần sửa:** mục 1.2.1, các use case đang gán cho tác nhân "Người bán", và Bảng 41
(danh sách giao diện).

**Thay bằng:**

```
Grocerly là website bán thực phẩm và tạp hóa trực tuyến của một siêu thị duy
nhất, theo mô hình bán lẻ một chủ tương tự Bách Hóa Xanh hay Co.opmart, không
phải sàn thương mại điện tử nhiều người bán như Shopee.

Trong hệ thống, "Nhà cung cấp" (Vendor) là thuộc tính thương hiệu của sản phẩm
— ví dụ Vinamilk, Coca-Cola, Masan — do nhân viên chọn khi đăng sản phẩm. Đây
không phải một tác nhân có tài khoản đăng nhập và không có khái niệm gian hàng
riêng. Người vận hành hệ thống là Nhân viên cửa hàng, làm việc trên toàn bộ dữ
liệu của siêu thị.
```

**Lợi ích kèm theo:** sửa xong thì mục *"Nhân viên chỉ thấy dữ liệu thuộc gian hàng
mình"* (mục 1.2.1) không còn là khoảng cách B1 trong [SPEC-GAPS](../SPEC-GAPS.md) nữa —
báo cáo và code khớp nhau.

**Nhất quán với phần khảo sát:** chính báo cáo đã đặt Grocerly cạnh Bách Hóa Xanh và
Co.opmart ở chương khảo sát hiện trạng, nên sửa theo hướng này làm chương 1 và chương 2
thống nhất với nhau hơn.
