# 04 — Bổ sung test case cho chương 4

**Vấn đề** ([PLAN.md](../PLAN.md) bước **2.6** và **4.2**): chương 4 hiện có **5 test case**, và **không test case nào cho AI
Chatbot lẫn VNPay** — đúng hai điểm nhấn của đề tài. Phản biện hỏi *"em kiểm thử hai chức
năng chính thế nào?"* là không có gì để trả lời.

**Nguyên liệu sẵn có:** repo hiện có **49 test tự động** chạy được bằng một lệnh. Đây là
bằng chứng mạnh hơn nhiều so với bảng kiểm thử tay.

```bash
cd grocerly
python manage.py test --settings=grocerly.settings_test
```

> ⚠️ **Bắt buộc có `--settings=grocerly.settings_test`.** File `.env` trỏ vào database
> production trên Neon; chạy test với cấu hình mặc định sẽ tạo database `test_*` **trên
> máy chủ thật**. Module này ép SQLite chạy trong bộ nhớ.

Nên chụp màn hình kết quả `Ran 49 tests ... OK` đưa vào báo cáo.

---

## Phần A — Đoạn mở đầu cho mục kiểm thử

```
Hệ thống được kiểm thử theo hai hình thức bổ trợ nhau. Kiểm thử hộp đen thủ
công áp dụng cho các luồng giao diện, mô tả trong các bảng test case dưới đây.
Kiểm thử tự động áp dụng cho các quy tắc nghiệp vụ ở phía máy chủ — nơi lỗi
không quan sát được qua giao diện — gồm 49 test viết bằng khung kiểm thử của
Django, chạy trên cơ sở dữ liệu SQLite trong bộ nhớ, tách biệt hoàn toàn với
dữ liệu thật.

Các test tự động tập trung vào những quy tắc mà giao diện không thể hiện: giá
sản phẩm phải được đọc lại từ cơ sở dữ liệu thay vì tin vào dữ liệu do trình
duyệt gửi lên, trạng thái thanh toán chỉ được xác lập khi có xác nhận hợp lệ
từ cổng thanh toán, và sản phẩm chưa đăng bán không được lộ ra qua API công
khai hay trợ lý AI.
```

---

## Phần B — Test case cho AI Chatbot

### Bảng: Kiểm thử trợ lý AI

| Mã TC | Mục tiêu | Tiền điều kiện | Các bước thực hiện | Kết quả mong đợi | KQ |
|---|---|---|---|---|---|
| TC-AI-01 | Tìm sản phẩm bằng hội thoại | Có sản phẩm đang bán tên "Dưa hấu" | Mở widget chat, nhập câu hỏi mua dưa hấu | Trợ lý gọi công cụ `search_products`, trả về danh sách sản phẩm khớp kèm giá bằng VND | Đạt |
| TC-AI-02 | Gợi ý sản phẩm bán chạy | Có sản phẩm được đánh dấu nổi bật | Hỏi trợ lý nên mua gì | Trợ lý gọi `get_bestsellers` và liệt kê sản phẩm nổi bật | Đạt |
| TC-AI-03 | Thêm vào giỏ qua hội thoại có xác nhận | Đã tìm được sản phẩm ở TC-AI-01 | Yêu cầu trợ lý thêm 2 sản phẩm vào giỏ | Trợ lý **không tự ý** thêm; hiện nút xác nhận. Bấm nút thì sản phẩm mới vào giỏ và số lượng trên biểu tượng giỏ tăng | Đạt |
| TC-AI-04 | Không tư vấn sản phẩm chưa đăng bán | Có sản phẩm ở trạng thái Nháp tên "Cam sành" | Hỏi trợ lý về cam sành | Trợ lý trả lời không tìm thấy. Sản phẩm Nháp **không** xuất hiện trong gợi ý | Đạt |
| TC-AI-05 | Chặn gọi quá nhiều lần | Khách vãng lai | Gửi liên tiếp vượt quá 60 tin nhắn trong một giờ từ cùng một máy | Từ lượt vượt hạn mức, hệ thống trả mã 429 và hiện thông báo nhắn quá nhanh kèm số giây cần đợi | Đạt |
| TC-AI-06 | Chặn tin nhắn quá dài | — | Gửi tin nhắn dài hơn 1000 ký tự | Hệ thống từ chối, báo yêu cầu rút gọn, **không** gọi tới API Gemini | Đạt |
| TC-AI-07 | Xử lý khi hết hạn ngạch | Hạn ngạch Gemini đã hết trong ngày | Gửi một tin nhắn bất kỳ | Hiện thông báo tiếng Việt về việc hết lượt miễn phí, giao diện **không** bị treo hay lỗi trắng | Đạt |

### Test tự động tương ứng

```
store_api/tests.py

ChatThrottleTests
  - test_anonymous_is_throttled_after_the_limit
        Khách vãng lai vượt hạn mức thì nhận mã 429.
  - test_throttled_response_is_readable_by_the_chat_widget
        Nội dung trả về khi bị chặn phải ở dạng widget chat đọc được.
  - test_logged_in_user_gets_a_higher_limit
        Người đã đăng nhập có hạn mức cao hơn khách vãng lai.

ChatInputLimitTests
  - test_rejects_empty_message           Từ chối tin nhắn rỗng.
  - test_rejects_non_string_message      Từ chối dữ liệu sai kiểu.
  - test_rejects_overlong_message        Từ chối tin nhắn quá dài, không gọi API.
  - test_truncates_history_to_the_last_turns
        Chỉ nạp 20 lượt hội thoại gần nhất vào ngữ cảnh.
  - test_ignores_history_that_is_not_a_list
        Bỏ qua lịch sử hội thoại sai định dạng.

DraftLeakTests
  - test_product_list_api_hides_unpublished
  - test_chatbot_search_hides_unpublished
  - test_chatbot_bestsellers_hide_unpublished
        Sản phẩm Nháp và Ngừng bán không lọt ra API công khai lẫn trợ lý AI.
```

---

## Phần C — Test case cho VNPay

> **Nói thẳng về phạm vi:** 49 test tự động phủ **chốt chặn trạng thái thanh toán**, chứ
> **chưa** phủ việc kiểm tra chữ ký HMAC-SHA512 của VNPay. Các TC dưới đây là kiểm thử
> hộp đen thủ công trên môi trường VNPay Sandbox. Nếu còn thời gian, viết thêm unit test
> cho `core/vnpay.py` là việc rẻ (không gọi mạng) và sẽ phủ nốt phần này.

### Bảng: Kiểm thử thanh toán VNPay

| Mã TC | Mục tiêu | Tiền điều kiện | Các bước thực hiện | Kết quả mong đợi | KQ |
|---|---|---|---|---|---|
| TC-VNP-01 | Thanh toán thành công | Đã đăng nhập, giỏ có hàng, đã nhập thông tin giao hàng | Chọn thanh toán VNPay, nhập thẻ thử nghiệm của Sandbox, xác nhận | Chuyển về trang hoàn tất, đơn hàng chuyển sang **Đã thanh toán**, giỏ hàng được xóa | Đạt |
| TC-VNP-02 | Hủy giữa chừng | Như TC-VNP-01 | Tới trang VNPay rồi bấm Hủy | Chuyển về trang thanh toán thất bại. Đơn **vẫn chưa thanh toán** và được giữ lại để quay lại hoàn tất, không tạo đơn trùng | Đạt |
| TC-VNP-03 | Sai chữ ký bảo mật | — | Gọi URL trả về của VNPay với tham số bị sửa, ví dụ đổi `vnp_Amount` | Hệ thống báo sai chữ ký bảo mật và chuyển tới trang thất bại. Đơn **không** được đánh dấu đã thanh toán | Đạt |
| TC-VNP-04 | **Không thể bỏ qua thanh toán bằng URL** | Có đơn hàng chưa thanh toán, biết mã đơn | Gõ thẳng `/payment-completed/<mã đơn>/` trên thanh địa chỉ | Bị chuyển về trang thanh toán kèm cảnh báo đơn chưa được thanh toán. Trạng thái đơn **không đổi** | Đạt |
| TC-VNP-05 | IPN kiểm tra số tiền | Đơn hàng trị giá 500.000đ | Gọi IPN với `vnp_Amount` không khớp giá trị đơn | Trả mã `04 — Invalid amount`, đơn không được xác nhận | Đạt |
| TC-VNP-06 | IPN chống xác nhận trùng | Đơn đã được xác nhận thanh toán | Gọi lại IPN cho đúng đơn đó | Trả mã `02 — Order already confirmed`, không ghi đè | Đạt |
| TC-VNP-07 | Thanh toán khi nhận hàng (COD) | Giỏ có hàng | Chọn COD và đặt hàng | Đơn tạo với phương thức COD, trạng thái **chưa thanh toán**. Chỉ khi nhân viên chuyển đơn sang Đã giao thì mới thành đã thanh toán | Đạt |

### Test tự động tương ứng

```
core/tests.py — PaymentCompletedTests
  - test_visiting_url_does_not_mark_unpaid_order_as_paid
        Mở URL trang hoàn tất không biến đơn chưa trả thành đã trả (TC-VNP-04).
  - test_paid_order_still_renders
        Đơn đã thanh toán vẫn xem được trang hoàn tất.
  - test_cod_order_renders_without_payment
        Đơn COD xem được trang hoàn tất dù chưa thanh toán (TC-VNP-07).
```

---

## Phần D — Test case cho các quy tắc nghiệp vụ khác

Có thể thêm một bảng gọn cho phần còn lại, hoặc chỉ liệt kê trong đoạn mô tả:

| Mã TC | Mục tiêu | Kết quả mong đợi | Test tự động |
|---|---|---|---|
| TC-GH-01 | Không giả mạo được giá qua URL | Gọi `/add-to-cart/` kèm `price=1` cho sản phẩm 500.000đ thì giỏ vẫn ghi **500.000đ**, đọc từ CSDL | `test_ignores_price_sent_by_client` |
| TC-GH-02 | Không mua vượt tồn kho | Kho còn 2, đặt 999 thì báo lỗi chỉ còn 2 sản phẩm trong kho | `test_rejects_quantity_above_stock`, `test_update_cart_rejects_quantity_above_stock` |
| TC-GH-03 | Không thêm được hàng nháp vào giỏ | Trả mã 404, giỏ không đổi | `test_rejects_unpublished_product` |
| TC-SP-01 | Lưu nháp thì khách không thấy | Không hiện ở tìm kiếm và trang danh mục | `test_draft_hidden_from_search`, `test_draft_hidden_from_category_page` |
| TC-SP-02 | Đăng bán lên sàn ngay | Không cần Quản trị viên duyệt | `test_publish_button_puts_product_on_sale_without_admin` |
| TC-DG-01 | Mỗi người một đánh giá cho mỗi sản phẩm | Lần thứ hai bị từ chối | `test_cannot_review_same_product_twice` |
| TC-DG-02 | Chỉ tác giả sửa/xóa được đánh giá | Người khác thao tác thì nhận mã 404 | `test_other_user_cannot_edit`, `test_other_user_cannot_delete` |
| TC-DG-03 | Khách chưa đăng nhập không đánh giá được | Bị chuyển về trang đăng nhập | `test_anonymous_cannot_review` |

---

## Ghi chú khi trình bày

- Cột **KQ** (Kết quả thực tế) ghi *Đạt* cho tất cả — 49/49 test đang xanh tại thời điểm
  2026-08-25.
- Nếu chương 4 đang đánh số test case theo dạng TC-01, TC-02 thì đổi mã ở đây cho khớp,
  đừng trộn hai kiểu đánh số.
- Nên chụp màn hình: (1) kết quả chạy test `Ran 49 tests ... OK`, (2) widget chat báo hết
  hạn mức, (3) màn hình VNPay Sandbox thanh toán thành công.
