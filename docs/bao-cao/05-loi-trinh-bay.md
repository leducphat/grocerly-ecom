# 05 — Lỗi trình bày và đánh số

Backlog **H** cộng nhóm **C** trong [SPEC-GAPS.md](../SPEC-GAPS.md). Toàn bộ là lỗi soạn
thảo, không liên quan tới code — nhưng là loại lỗi phản biện dễ chỉ ra nhất vì không cần
đọc code cũng thấy.

| # | Vị trí | Lỗi | Cách sửa |
|---|---|---|---|
| C1 | tr.54 và tr.67 | Hai mục cùng đánh số **3.5** | Đổi mục sau thành **3.6** |
| C2 | tr.92 | Caption ghi *"Hình 3.5.23"*, và hình này **thiếu trong Danh mục hình ảnh** | Đánh lại số cho đúng dãy, bổ sung vào danh mục |
| C3 | tr.6 | Câu lỗi logic về Shopee | Viết lại, xem bên dưới |
| C4 | tr.3 vs tr.33 | Tên Chương 2 không khớp giữa mục lục và thân bài | Thống nhất một tên |
| C5 | tr.1 | Lời cảm ơn ký *"Nhóm sinh viên"* nhưng là đồ án cá nhân | Đổi thành ngôi thứ nhất số ít |
| C6 | Chương 2 | Thiếu một số công nghệ đang thực sự dùng | Bổ sung, xem bên dưới |
| C7 | Chương 4 | Chỉ có 5 test case | Xem [04-chuong-4-test-case.md](04-chuong-4-test-case.md) |
| C8 | tr.108 | In mật khẩu 3 tài khoản production | Xem cuối file |

---

## C1 — Trùng số mục 3.5

Hai mục cùng mang số **3.5**: *Thiết kế cơ sở dữ liệu* (tr.54) và *Thiết kế giao diện*
(tr.67). Mục sau phải là **3.6**, kéo theo các mục con `3.5.1`/`3.5.2` của nó thành
`3.6.1`/`3.6.2`.

Sau khi đổi, kiểm lại **mục lục** và mọi câu trích dẫn dạng *"xem mục 3.5"* trong thân bài
— câu nào đang trỏ tới phần giao diện thì phải đổi theo.

---

## C2 — Caption sai ở tr.92

Caption đang ghi *"Hình 3.5.23"* trong khi toàn báo cáo đánh số hình liên tục (Hình 1,
Hình 2, ...). Hình này cũng **thiếu hẳn** trong Danh mục hình ảnh — danh mục nhảy từ Hình
71 (tr.91) sang Hình 72 (tr.93).

Sửa caption về đúng dãy số và bổ sung dòng tương ứng vào Danh mục hình ảnh.

> Làm mục này **sau** bước 4.3 ở [01-bo-luong-duyet-san-pham.md](01-bo-luong-duyet-san-pham.md)
> (xóa Hình 40), vì bước đó làm lùi số thứ tự của mọi hình phía sau.

---

## C3 — Câu lỗi logic ở tr.6

**Câu hiện tại** (đại ý): *"Shopee là một phân nhánh chiến lược của nền tảng thương mại
điện tử khổng lồ Shopee"* — định nghĩa vòng, lấy chính nó giải thích chính nó.

**Thay bằng** (nếu ý ban đầu là nói về ShopeeFood hoặc mảng bách hóa của Shopee):

```
Shopee Mart là mảng bách hóa nằm trong hệ sinh thái của sàn thương mại điện tử
Shopee, tận dụng sẵn lượng người dùng và hạ tầng logistics của nền tảng mẹ để
mở rộng sang nhóm hàng tiêu dùng nhanh.
```

> Kiểm lại ý gốc bạn định viết rồi chỉnh, vì tôi không đọc được ngữ cảnh đoạn văn.

---

## C4 — Tên Chương 2 không khớp

| Vị trí | Đang ghi |
|---|---|
| tr.3 (mục lục / đề cương) | *"...và quy trình phát triển hệ thống"* |
| tr.33 (thân bài) | *"...và cơ sở lý thuyết"* |

Chọn **một** tên rồi sửa chỗ còn lại cho khớp. Xét nội dung chương 2 thực tế đang trình
bày công nghệ và nền tảng, *"Cơ sở lý thuyết và công nghệ sử dụng"* sát hơn.

---

## C5 — Lời cảm ơn ở tr.1

Đang ký **"Nhóm sinh viên"** nhưng đây là tiểu luận cá nhân. Sửa toàn bộ đoạn về ngôi thứ
nhất số ít — chú ý cả các cụm *"chúng em"*, *"nhóm chúng em"* rải trong đoạn.

```
Em xin chân thành cảm ơn ...

                                          Sinh viên thực hiện
                                            Lê Đức Phát
```

---

## C6 — Chương 2 thiếu công nghệ đang dùng

Bốn thứ đang được dùng thật trong code nhưng chương 2 không nhắc tới:

```
Django REST Framework

Django REST Framework là thư viện mở rộng của Django dùng để xây dựng API theo
kiến trúc REST. Trong hệ thống Grocerly, thư viện này là nền tảng cho toàn bộ
nhóm địa chỉ /api/v1/ phục vụ trợ lý AI, bao gồm việc chuyển đổi dữ liệu mô
hình sang JSON qua lớp Serializer và cơ chế giới hạn tần suất truy cập
(throttling) nhằm bảo vệ hạn ngạch gọi API của dịch vụ AI.

Django i18n và GNU gettext

Hệ thống hỗ trợ song ngữ Việt - Anh thông qua cơ chế đa ngôn ngữ sẵn có của
Django kết hợp công cụ GNU gettext. Các chuỗi hiển thị được đánh dấu trong mã
nguồn và biên dịch thành tệp thông điệp, cho phép chuyển ngôn ngữ mà không cần
sửa mã. Địa chỉ trang có tiền tố ngôn ngữ, ví dụ /vi/ và /en/.

WhiteNoise

WhiteNoise cho phép ứng dụng Django tự phục vụ tệp tĩnh trong môi trường
triển khai mà không cần dựng thêm máy chủ web riêng, phù hợp với mô hình triển
khai trên nền tảng Render mà đề tài sử dụng.

django-taggit

django-taggit quản lý nhãn (tag) của sản phẩm. Dữ liệu nhãn được lưu ở các
bảng riêng do thư viện tạo ra, không phải một cột trong bảng sản phẩm.
```

> Ý cuối về django-taggit cũng sửa luôn khoảng cách **B4** và **B5** trong
> [SPEC-GAPS](../SPEC-GAPS.md): ERD (Hình 45) đang vẽ `core_product.tags` như một cột
> `VARCHAR`, và Bảng 28 mô tả `core_tag` như bảng thật trong khi model đó rỗng, không
> dùng. Nếu sửa được ERD thì bỏ `core_tag` và vẽ đúng hai bảng của taggit, đồng thời bổ
> sung bảng nối nhiều-nhiều giữa `cartorder` và `coupon` mà ERD đang thiếu.

---

## C8 — Mật khẩu tài khoản production ở tr.108

Trang 108 in nguyên văn mật khẩu của **ba tài khoản đang chạy thật** (Quản trị viên, Nhân
viên, Khách hàng), ngay cạnh link tới repo GitHub **công khai**.

Việc in tài khoản demo để giảng viên tiện chấm là hợp lý. Vấn đề là **đúng ba tài khoản
đó đang sống trên site production**.

**Xử lý sau khi bảo vệ xong** — đây là backlog K:

1. Đổi mật khẩu cả ba tài khoản.
2. Nếu muốn giữ tài khoản demo cho người xem repo, tạo tài khoản riêng **quyền hạn chế**,
   tuyệt đối không phải superuser.

Trong bản nộp thì cứ giữ nguyên để chấm bài, nhưng nên biết đây là rủi ro đã được ghi
nhận — xem [SECURITY.md](../SECURITY.md) mục S-06.
