# Nhật ký quyết định kiến trúc (ADR)

Mỗi mục ghi lại **một quyết định**, bối cảnh dẫn tới nó và hệ quả. Mục đích: sáu tháng
sau đọc lại vẫn hiểu *tại sao* code lại như vậy, thay vì phải suy đoán.

Trạng thái: `Đã chốt` · `Đề xuất` · `Thay thế bởi ADR-XXXX`

---

## ADR-0001 — Giữ hai vai trò Quản trị viên và Nhân viên

**Trạng thái:** Đã chốt · 2026-08-20

### Bối cảnh

Quyền của Admin đang **bao trùm hoàn toàn** quyền của Staff: `admin_required` chấp nhận
cả `is_superuser` lẫn `is_staff`, và Admin còn có Django Admin console chỉnh được mọi
thứ. Câu hỏi đặt ra: hai vai trò chồng lấn như vậy có thừa không?

### Quyết định

**Giữ cả hai.** Overlap kiểu bao hàm là phân cấp vai trò bình thường, không phải lỗi
thiết kế. Ranh giới nằm ở **phạm vi thẩm quyền**, không ở khả năng kỹ thuật:

| | Nhân viên | Quản trị viên |
|---|---|---|
| Sản phẩm, tồn kho, đơn hàng | ✔ | ✔ (kế thừa) |
| Quản lý người dùng & phân quyền | ✘ | ✔ |
| Danh mục dùng chung | ✘ | ✔ |
| Mã giảm giá | ✘ | ✔ |
| Gỡ sản phẩm vi phạm, xem toàn bộ doanh thu | ✘ | ✔ |

### Lý do

1. **Đặc quyền tối thiểu** — nhân viên chạy ca không nên xóa được tài khoản hay đổi
   cấu hình thanh toán. Giảm thiệt hại khi lộ tài khoản.
2. **Truy vết trách nhiệm** — biết ai đổi giá, ai đổi trạng thái đơn.
3. **Trải nghiệm vận hành** — Django Admin quá tổng quát để xử lý đơn hàng hàng ngày;
   `useradmin` tối giản cho tác vụ lặp lại. Đây là lý do mạnh nhất cho việc tồn tại
   hai giao diện.
4. Đối chiếu thực tế: WooCommerce có role `Shop Manager`, Shopify có `Staff accounts`,
   Magento có ACL role — đều là quan hệ bao hàm với vai trò chủ hệ thống.

### Hệ quả

- Trong sơ đồ Use Case phải dùng **generalization giữa tác nhân** (Quản trị viên ─▷
  Nhân viên), **không** nhân đôi use case theo từng tác nhân.
- Quy tắc mô hình hóa: *hai use case có cùng Main Flow là một use case; khác tác nhân
  không sinh ra use case mới, khác luồng xử lý mới sinh ra.*
- Cần bổ sung generalization này vào Hình 4 của báo cáo (hiện đã áp dụng đúng cho cặp
  Khách hàng ─▷ Khách vãng lai, chỉ thiếu cặp còn lại).

---

## ADR-0002 — Bỏ quy trình duyệt sản phẩm (`in_review`)

**Trạng thái:** Đã chốt · 2026-08-20 · **Đã triển khai 2026-08-24** — code và
migration `0005_product_status_drop_review_flow` (đã áp lên production); phần sửa báo
cáo — [PLAN.md](PLAN.md) bước 3.3 — chưa làm

### Bối cảnh

`Product.STATUS` có 5 giá trị `draft / disabled / in_review / rejected / published`,
mặc định `in_review`. Báo cáo (UC 3.2.19, Hình 28) mô tả nhân viên đăng sản phẩm sẽ ở
trạng thái *"Chờ duyệt"* rồi Admin duyệt. Nhưng code
([useradmin/views.py:89](../grocerly/useradmin/views.py#L89)) đặt thẳng `'published'` —
quy trình duyệt **chưa từng được cài đặt**.

Phải chọn: cài cho đủ, hay bỏ hẳn?

### Quyết định

**Bỏ hẳn.** Rút còn ba trạng thái: `draft` / `published` / `disabled`, mặc định `draft`.

### Lý do

Nguyên tắc: *kiểm duyệt chỉ cần khi người đăng nội dung không chịu trách nhiệm hợp
đồng/pháp lý với chủ hệ thống.*

- **Sàn nhiều người bán** (Shopee, Etsy, Amazon 3P): người bán là bên ngoài, có thể bán
  hàng giả/hàng cấm → bắt buộc kiểm duyệt.
- **Cửa hàng một chủ** (Grocerly): người đăng là nhân viên có hợp đồng lao động, chịu
  trách nhiệm trực tiếp → kiểm duyệt chỉ thêm ma sát mà không giảm rủi ro. Nếu đã tin
  nhân viên đủ để cho họ sửa giá và đổi trạng thái đơn hàng, thì việc đăng sản phẩm
  không nguy hiểm hơn.

Đối chiếu sản phẩm thật: **WooCommerce và Shopify đều không có luồng duyệt sản phẩm.**
Trạng thái họ dùng là Draft/Published/Archived — do chính người đăng kiểm soát.

Chuỗi `in_review → rejected` nhiều khả năng được kế thừa từ template multi-vendor ban
đầu, cùng nguồn gốc với vấn đề `Vendor` ở ADR-0003.

### Phương án đã cân nhắc

| Phương án | Đánh giá |
|---|---|
| Cài đầy đủ luồng duyệt | Thêm 1 use case + 1 sequence diagram để "khoe" trong báo cáo, nhưng tạo ma sát vận hành không có lý do nghiệp vụ |
| **Bỏ, dùng draft/published** ✔ | Khớp best practice và khớp mô hình một cửa hàng |
| Chuyển quyền tạo sản phẩm lên Admin (mô hình merchandising tập trung của bán lẻ thật) | Đúng với ngành nhất, nhưng kéo theo sửa nhiều use case — quá tốn ở giai đoạn sắp bảo vệ |

### Hệ quả

- ADR-0001 vẫn đứng vững: hai vai trò được biện minh bằng **phạm vi thẩm quyền**, không
  phải bằng cổng duyệt.
- Nhân viên tự quyết **khi nào** sản phẩm sẵn sàng (nút "Lưu nháp" / "Đăng bán"), thay vì
  xin phép **có được đăng hay không**.
- Khi có `draft` thật, lỗ rò hàng nháp qua API/chatbot (S-04) trở thành lỗi thấy được →
  phải sửa cùng lượt.
- Báo cáo phải sửa: UC 3.2.19, UC 3.2.24, Hình 28, Hình 29, bỏ Hình 40, Bảng 30.

---

## ADR-0003 — `Vendor` là thương hiệu, không phải người bán có tài khoản

**Trạng thái:** **Đã chốt · 2026-08-25** (đề xuất 2026-08-20) · Hệ quả: báo cáo KLTN —
[PLAN.md](PLAN.md) giai đoạn 3

### Bối cảnh

Báo cáo mô tả Grocerly là hệ thống **multi-vendor**, "Người bán (Vendor/Nhân viên cửa
hàng)" đăng nhập để vận hành gian hàng riêng. Nhưng thực tế:

- Dữ liệu bảng `core_vendor`: *Grocerly Official, Suntory, Coca-Cola, Masan, Acecook,
  Vissan, CP, TH True Milk* — đều là **thương hiệu**, không phải merchant có tài khoản.
- [useradmin/forms.py:17](../grocerly/useradmin/forms.py#L17) cho nhân viên **chọn
  vendor bất kỳ** từ dropdown → vendor là thuộc tính sản phẩm, không phải chủ sở hữu.
- `useradmin` không lọc dữ liệu theo vendor: mọi staff thấy toàn bộ sản phẩm và doanh thu.
- `Vendor.user` chỉ được dùng làm giá trị dự phòng khi form không chọn vendor.

### Đề xuất

Thừa nhận đúng bản chất: Grocerly là **một siêu thị**, `Vendor` là **nhà cung cấp /
thương hiệu**. Đổi thuật ngữ trong báo cáo: "Người bán" → **"Nhân viên cửa hàng"**;
"Nhà cung cấp" giữ nghĩa thương hiệu.

### Hệ quả nếu chấp nhận

- Xóa được một mục nợ kỹ thuật: `useradmin` **không cần** giới hạn phạm vi theo vendor
  (vì không có khái niệm gian hàng riêng).
- Khớp với chính phần khảo sát của báo cáo — Grocerly được định vị cạnh Bách Hóa Xanh và
  Co.opmart (bán lẻ một chủ), không phải Shopee (sàn).
- Cần sửa mục 1.2.1, các use case của "Người bán", và Bảng 41 danh sách giao diện.

### Vì sao chốt (2026-08-25)

Đề xuất này treo ở trạng thái *Đề xuất* vì chạm tới định vị đề tài. Khi chuyển sang làm
Khóa luận tốt nghiệp, người thực hiện đồ án đã quyết định chốt.

Yếu tố quyết định: **chính báo cáo đã tự mâu thuẫn.** Chương 1 khảo sát Bách Hóa Xanh và
Co.opmart — hai chuỗi bán lẻ một chủ — rồi định vị Grocerly cạnh chúng; nhưng mục 1.2.1
lại mô tả "Người bán" có *"gian hàng mình"* kiểu sàn nhiều người bán. Giữ nguyên thì mâu
thuẫn đó nằm ngay trong cùng một chương.

Ngoài ra dữ liệu thật của bảng `core_vendor` (*Vinamilk, Coca-Cola, Masan, Acecook, CP,
TH True Milk*) là bằng chứng không chối được nếu bị hỏi.

---

## ADR-0004 — `AGENTS.md` là nguồn duy nhất cho chỉ dẫn AI

**Trạng thái:** Đã chốt · 2026-08-20

### Bối cảnh

Repo đã có `.github/copilot-instructions.md` viết từ giai đoạn đầu. Đến nay file này sai
gần như toàn bộ: nói dự án chỉ có 2 app (thực tế 4), SQLite là database mặc định (thực tế
PostgreSQL), *"chưa có requirements.txt"* (đã có từ lâu), và không hề nhắc tới DRF,
Gemini, VNPay, i18n hay soft delete.

Nay cần thêm chỉ dẫn cho Claude Code — nếu tạo thêm file độc lập nữa thì đến lượt nó
cũng sẽ lệch y hệt.

### Quyết định

- `AGENTS.md` (chuẩn mở, nhiều công cụ cùng đọc) chứa **toàn bộ** nội dung.
- `CLAUDE.md` import bằng cú pháp `@AGENTS.md`, chỉ giữ phần đặc thù Claude Code.
- `.github/copilot-instructions.md` rút gọn thành con trỏ về `AGENTS.md`.
- Thư mục `.claude/` (bộ công cụ ECC: skills, agents, commands) **được gitignore** — đó
  là công cụ cá nhân của lập trình viên, không phải mã nguồn dự án, và sẽ thêm ~780 file
  / 6.8 MB vào repo.

### Hệ quả

Sửa chỉ dẫn ở một chỗ duy nhất. Ba công cụ AI khác nhau đọc cùng một nội dung.

---

## ADR-0005 — Không cài điều kiện "đã mua mới được đánh giá"

**Trạng thái:** ~~Đã chốt · 2026-08-25~~ · **Thay thế bởi [ADR-0006](#adr-0006--thêm-khóa-ngoại-product-cho-cartorderitem)
cùng ngày**

> ⚠️ ADR này bị thay thế **vài giờ sau khi chốt**, do bối cảnh thay đổi chứ không phải do
> lập luận sai. Giữ lại nguyên văn vì phần phân tích hạn chế của mô hình dữ liệu vẫn đúng
> và chính là tiền đề của ADR-0006.

### Bối cảnh

UC 3.2.14 Pre-Conditions yêu cầu khách phải **đã mua hàng (đơn Shipped)** mới được đánh
giá. Code hiện chỉ chặn mỗi người một đánh giá cho mỗi sản phẩm.

Để cài điều kiện này phải trả lời được: *"người này đã mua sản phẩm kia chưa?"*. Nhưng
`CartOrderItem` **không có khóa ngoại tới `Product`** — nó lưu snapshot dạng chuỗi:

```python
class CartOrderItem(models.Model):
    order = models.ForeignKey(CartOrder, ...)
    item = models.CharField(max_length=200)   # chỉ có TÊN sản phẩm
```

Snapshot là thiết kế **có chủ ý** (hóa đơn không đổi khi sản phẩm bị sửa hay xóa), nhưng
hệ quả là không truy ngược được về sản phẩm gốc.

### Quyết định

**Không cài.** Chuyển yêu cầu này xuống mục *Hướng phát triển* của báo cáo.

### Lý do

Chỉ còn cách so khớp theo tên — đúng nguồn gốc nợ kỹ thuật #6 ở
[ARCHITECTURE.md](ARCHITECTURE.md) (`change_order_status` trừ kho sai khi trùng tên).
Hai lỗi âm thầm đi kèm:

- Nhân viên **sửa tên sản phẩm** sau khi bán → người mua thật **mất quyền đánh giá**
- Hai sản phẩm **trùng tên** → mua cái này lại đánh giá được cái kia

Sai kiểu này tệ hơn là không có điều kiện: nó chặn nhầm người dùng hợp lệ mà không báo
lý do, và chỉ lộ ra khi ai đó đổi tên sản phẩm.

Thêm nữa, bật điều kiện lên thì muốn demo chức năng đánh giá phải dựng sẵn đơn đã giao —
thêm ma sát cho đúng buổi bảo vệ.

### Phương án đã cân nhắc

| Phương án | Đánh giá |
|---|---|
| Khớp theo tên | Không migration, nhưng chặn nhầm người mua thật khi tên đổi |
| Thêm FK `Product` vào `CartOrderItem` | Đúng dữ liệu và vá luôn nợ #6, nhưng phải sửa `save_checkout_info` — luồng rủi ro nhất, lại có sequence diagram trong báo cáo — cộng một migration nữa lên production ngay trước bảo vệ |
| **Bỏ, sửa báo cáo** ✔ | Nhất quán với [ADR-0002](DECISIONS.md): khi code và báo cáo lệch nhau, sửa bên nào rẻ và đúng hơn |

### Hệ quả

- Ai đăng nhập cũng đánh giá được, mỗi người một lần cho mỗi sản phẩm.
- Nếu sau này muốn cài, **việc cần làm trước là thêm FK** cho `CartOrderItem`, không phải
  viết thêm điều kiện ở view.
- Báo cáo phải sửa UC 3.2.14 Pre-Conditions. Phần *Sửa & Xóa đánh giá* của cùng use
  case thì giữ nguyên, đã cài xong 2026-08-25.

> Hệ quả này **không còn hiệu lực** sau [ADR-0006](#adr-0006--thêm-khóa-ngoại-product-cho-cartorderitem):
> báo cáo giữ nguyên cả Bảng 14 lẫn Hình 21.

---

## ADR-0006 — Thêm khóa ngoại `Product` cho `CartOrderItem`

**Trạng thái:** Đã chốt · 2026-08-25 · **Đã cài xong 2026-08-26** · Thay thế [ADR-0005](#adr-0005--không-cài-điều-kiện-đã-mua-mới-được-đánh-giá)

### Bối cảnh

[ADR-0005](#adr-0005--không-cài-điều-kiện-đã-mua-mới-được-đánh-giá) quyết định **không**
cài điều kiện "đã mua mới được đánh giá", vì `CartOrderItem` chỉ lưu tên sản phẩm dạng
chuỗi nên không trả lời tin cậy được câu *"người này đã mua sản phẩm kia chưa"*.

Phần phân tích đó **vẫn đúng**. Cái thay đổi là **lý do loại phương án thêm khóa ngoại**.
ADR-0005 loại nó vì:

> *"phải sửa `save_checkout_info` — luồng rủi ro nhất, lại có sequence diagram trong báo
> cáo — cộng một migration nữa lên production ngay trước bảo vệ"*

Cả ba vế đều là **ràng buộc thời gian của kỳ bảo vệ Tiểu luận chuyên ngành**. Tiểu luận
đã nộp và có điểm; công việc hiện tại là Khóa luận tốt nghiệp với thời hạn trên ba tháng.
Ràng buộc đã biến mất, nên quyết định phải được xét lại thay vì kế thừa quán tính.

### Quyết định

**Thêm `product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)` vào
`CartOrderItem`**, song song với bản sao tĩnh (`item`, `image`, `price`) đang có.

Không bỏ bản sao tĩnh: nó phục vụ hóa đơn, phải giữ nguyên khi sản phẩm bị sửa hoặc xóa.
Khóa ngoại là **thông tin truy vết bổ sung**, không phải vật thay thế.

### Lý do

1. **Mở đường cho A2.** Điều kiện "đã mua mới được đánh giá" (UC 3.2.14) khi đó kiểm tra
   được chính xác, thay vì so khớp theo tên và chặn nhầm người mua thật khi sản phẩm đổi
   tên.
2. **Vá nợ kỹ thuật #6.** `change_order_status` đang trừ tồn kho bằng
   `Product.objects.filter(title=item.item)` — trừ nhầm sản phẩm khi hai sản phẩm trùng
   tên. Đây là lỗi **đang tồn tại**, không phải lỗi giả định.
3. **Báo cáo giữ nguyên được.** Bảng 14 và Hình 21 đã mô tả sẵn điều kiện đã mua. Làm
   theo hướng này thì không phải sửa hai chỗ đó — ngược hẳn với ADR-0005.

### Hệ quả

- ✅ `save_checkout_info` gán `product` khi tạo `CartOrderItem`. Hóa ra tra ngược còn
  thẳng hơn dự tính: **khóa của giỏ hàng chính là khóa chính của sản phẩm**, không cần đi
  vòng qua `pid`.
- ✅ Migration `0007` có **backfill theo tên** — nhưng chốt chặt hơn mô tả ban đầu: chỉ
  nối khi tên ứng với **đúng một** sản phẩm. Tên trùng hai sản phẩm thì để `NULL` chứ
  không chọn bừa, vì nối sai một dòng hóa đơn về nhầm sản phẩm là cái sai im lặng mà các
  bước sau sẽ tin là đúng.
- ⏳ ERD (Hình 45) và Bảng 33 phải bổ sung khóa ngoại này — [PLAN.md](PLAN.md) bước 3.8,
  **chưa làm**.
- ✅ **SPEC-GAPS A2 đã đóng** (2026-08-26). Việc sửa UC 3.2.14 Pre-Conditions trong kế
  hoạch cũ bị hủy: báo cáo đã mô tả đúng ngay từ đầu.

### Ghi chú cho báo cáo

Cặp ADR-0005 → ADR-0006 là ví dụ tốt cho mục *Quyết định kiến trúc* của KLTN: cùng một
dữ kiện kỹ thuật, hai kết luận khác nhau vì ràng buộc dự án khác nhau — và quyết định
được xét lại khi ràng buộc mất đi, thay vì kế thừa theo quán tính.

Sau khi cài xong (2026-08-26) cặp ADR này còn có thêm một kết cục kiểm chứng được. Lý do
ADR-0005 loại phương án — *"đổi tên sản phẩm là chặn nhầm người mua thật"* — nay là một
test chạy được: `RenameAndDeleteTests` trong
[core/test_review_purchase.py](../grocerly/core/test_review_purchase.py). Không chỉ nói
rằng quyết định cũ đã hết hiệu lực, mà chứng minh được.

Một chi tiết nữa đáng đưa vào báo cáo: cùng một dữ liệu thiếu (`product IS NULL`), code
xử lý **ba cách khác nhau** tùy hướng của rủi ro. `product_has_order_history` vẫn so tên
(đoán sai → xóa mềm, khôi phục được); `change_order_status` bỏ qua (đoán sai → trừ nhầm
kho người khác); `has_purchased` từ chối (đoán sai → mở quyền đánh giá cho người chưa
mua). Không có một quy tắc chung nào đúng cho cả ba.

---

## ADR-0007 — Hủy đơn chỉ áp dụng cho đơn chưa thanh toán và chưa xuất kho

**Trạng thái:** Đã chốt · 2026-08-26

### Bối cảnh

UC 3.2.25 mô tả chức năng "Hủy đơn" nhưng `STATUS_CHOICES` chỉ có ba giá trị
`processing`/`shipped`/`delivered`, nên không có gì để demo ([SPEC-GAPS A7](SPEC-GAPS.md)).
Bản Tiểu luận xử lý bằng cách đề xuất **bỏ use case** khỏi báo cáo — xem
[bao-cao/06](bao-cao/06-huong-phat-trien.md). KLTN đảo nguyên tắc đó và cài cho xong.

Câu hỏi thật không phải *"thêm trạng thái `cancelled`"* — việc đó là một dòng. Câu hỏi là
**hủy được từ đâu tới đâu**, vì mỗi câu trả lời kéo theo một luồng nghiệp vụ khác nhau.

Bản báo cáo không nói rõ ai hủy và hủy lúc nào, nên đây là chỗ **phải tự quyết**.

### Quyết định

Hủy được khi và chỉ khi đơn thỏa **cả hai**:

1. `product_status == 'processing'` — chưa xuất kho.
2. `paid_status == False` — chưa thu tiền.

`cancelled` là trạng thái **cuối**, ngang hàng `delivered`. Cả khách lẫn nhân viên đều
hủy được, cùng một bộ điều kiện.

### Lý do

**Điều kiện 1 làm biến mất nhánh hoàn kho.** Tồn kho chỉ bị trừ đúng một chỗ:
`change_order_status` khi đơn chuyển sang `shipped`. Giới hạn việc hủy ở trước mốc đó
nghĩa là **không có gì để hoàn** — không phải "hoàn kho đúng", mà là *không tồn tại nhánh
hoàn kho nào để viết sai*. Đây là cách rẻ nhất để tránh một lớp lỗi số liệu âm thầm, và
là bài học rút từ chính nợ kỹ thuật #6: chỗ trừ kho cũ đã sai suốt mà không ai biết.

**Điều kiện 2 tránh hứa một chức năng không có.** Hủy đơn đã trả tiền hàm ý hoàn tiền.
VNPay ở đây chỉ tích hợp **chiều thu** — không có API hoàn, không có luồng đối soát, không
có trạng thái "đang hoàn tiền". Cho khách bấm Hủy trên một đơn đã trả là tạo ra một đơn
vừa hủy vừa đã thu tiền, và không có màn hình nào xử lý được tình trạng đó.

Đơn COD **không** bị điều kiện 2 chặn: `paid_status` của COD chỉ bật khi giao tới tay
khách, nên đơn COD đang xử lý luôn hủy được. Đây là phần lớn đơn thực tế.

### Phương án đã cân nhắc

| Phương án | Đánh giá |
|---|---|
| **Chỉ hủy `processing` + chưa trả tiền** ✔ | Không cần hoàn kho, không cần hoàn tiền. Đánh đổi: khách trả VNPay xong đổi ý thì phải liên hệ nhân viên |
| Cho hủy cả `shipped`, kèm hoàn kho | Đúng nghiệp vụ hơn nhưng phải viết nhánh cộng lại tồn kho — mà hàng đã rời kho thật, cộng lại là sai số liệu theo chiều ngược |
| Cho hủy đơn đã trả, đánh dấu "chờ hoàn tiền" | Thêm một trạng thái nữa cho một luồng **không có ai xử lý**. Trạng thái treo vĩnh viễn còn tệ hơn là không cho hủy |
| Chỉ nhân viên được hủy | Giảm được điều kiện 2, nhưng UC 3.2.25 nằm ở nhóm chức năng của khách và đây là thao tác khách mong đợi nhất |

### Hệ quả

- Ba đường có thể hồi sinh một đơn đã hủy, và **cả ba đều phải chặn**: `place_cod_order`
  và `vnpay_payment` gán thẳng `product_status = 'processing'`;
  `_get_pending_order_from_session` tái sử dụng đơn treo cho lần thanh toán sau. Chốt thứ
  ba là chỗ dễ sót nhất vì nó chỉ lộ ra khi **nhân viên** hủy (khách tự hủy thì session
  đã được dọn) — [core/test_cancel_order.py](../grocerly/core/test_cancel_order.py) có
  test riêng cho đúng kịch bản đó.
- `cancelled` vào `STATUS_CHOICES` nên nó **tự động** xuất hiện trong dropdown của nhân
  viên (dropdown dựng từ model). Đó là điều mong muốn, nhưng nghĩa là whitelist giá trị
  hợp lệ **không đủ** — phải có thêm chốt riêng cho *bước chuyển*, vì `cancelled` là giá
  trị hợp lệ mà không phải bước chuyển hợp lệ từ mọi trạng thái.
- Migration `0008` là `AlterField` trên `choices`, `sqlmigrate` xác nhận **no-op DDL** —
  an toàn với dữ liệu production, giống migration `0005`.
- Báo cáo: UC 3.2.25 giữ nguyên được phần lớn, nhưng **phải bổ sung hai tiền điều kiện**
  này vào Pre-Conditions. Đây là chỗ code hẹp hơn báo cáo, ngược với A2.

### Ghi chú cho báo cáo

Đáng đưa vào mục *Quyết định kiến trúc*: cả hai điều kiện đều được chọn không phải vì
chúng đúng về nghiệp vụ hơn, mà vì chúng **xóa bỏ một lớp lỗi** thay vì phải phòng thủ
trước lớp lỗi đó. Không có nhánh hoàn kho thì không hoàn kho sai được; không có đơn vừa
hủy vừa đã thu tiền thì không cần màn hình xử lý nó.

---

## ADR-0008 — Đơn đã chuyển sang cổng thanh toán thì khóa giá

**Trạng thái:** Đã chốt · 2026-08-26

### Bối cảnh

[S-13](SECURITY.md): `vnpay_payment` chốt số tiền **tại thời điểm chuyển hướng**
(`amount = int(order.price) * 100`), còn `vnpay_ipn` lại đối chiếu callback với
`order.price` **đang có trong database lúc nhận**. Hai con số đó lệch nhau được.

Khi lệch, IPN trả `'04' Invalid amount` và đơn **không bao giờ được đánh dấu đã thanh
toán** — dù khách đã mất tiền thật. `used_count` của mã giảm giá cũng không tăng theo.

Đường đi tới chỗ lệch có sẵn: mở `/checkout/<oid>/` ở tab khác rồi áp thêm mã giảm giá
sau khi đã bấm sang VNPay. Bản vá bước 2.9/2.10 đã bịt đường tương tự cho đơn COD
(`checkout()` từ chối đơn `payment_method == 'cod'`), nhưng đơn online đã sang cổng thì
`payment_method` vẫn là `'online'` nên không có dấu hiệu nào để chặn.

### Quyết định

Thêm `CartOrder.vnpay_amount` — số tiền đã gửi sang cổng, theo đúng đơn vị VNPay dùng
(VND × 100). Ghi ở `vnpay_payment`, mỗi lần chuyển hướng ghi đè lần trước.

Từ đó ra hai chốt:

1. **`vnpay_ipn` đối chiếu với `vnpay_amount`**, không tính lại từ `order.price`.
   `NULL` (đơn COD, hoặc đơn có từ trước migration `0011`) thì rơi về hành vi cũ.
2. **`checkout()` từ chối mọi đơn có `vnpay_amount is not None`** — giá bị khóa sau khi
   đã sang cổng.

### Lý do

**Chốt 1 sửa đúng chỗ sai.** Câu hỏi mà IPN phải trả lời là *"số tiền cổng báo có đúng
bằng số ta đã yêu cầu không"*. Tính lại từ `order.price` là trả lời một câu hỏi khác —
*"có đúng bằng giá đơn bây giờ không"* — và hai câu đó chỉ trùng nhau khi giá không đổi.
Lưu lại con số đã gửi làm câu hỏi thứ nhất trả lời được trực tiếp, không phải suy ra.

**Chốt 2 mới là chỗ phải cân nhắc.** Chỉ có chốt 1 thì đơn vẫn được ghi nhận đã trả, nhưng
`order.price` nói một con số còn số khách thật sự trả nói một nẻo — và không có luồng hoàn
tiền nào để chỉnh lại ([ADR-0007](#adr-0007--hủy-đơn-chỉ-áp-dụng-cho-đơn-chưa-thanh-toán-và-chưa-xuất-kho)).
Khóa giá là cách duy nhất giữ hai con số bằng nhau.

Cùng một logic với `payment_method == 'cod'` ngay bên trên nó: *đơn đã rời khỏi tay khách
thì không hạ giá được nữa*, chỉ khác dấu hiệu nhận biết.

### Phương án đã cân nhắc

| Phương án | Đánh giá |
|---|---|
| **Lưu số đã gửi + khóa giá sau khi sang cổng** ✔ | Giữ `order.price` luôn bằng số khách trả. Đánh đổi: khách bỏ dở ở VNPay rồi đổi ý thì không áp thêm mã cho đơn đó được nữa |
| Chỉ lưu số đã gửi, không khóa giá | Đơn được ghi nhận đã trả đúng, nhưng sinh ra đơn có `price` khác số tiền thu được — mà không màn hình nào và không luồng nào xử lý được sự chênh đó |
| Xóa `vnpay_amount` mỗi khi giá đổi | Tệ hơn hẳn: khách **đã trả** theo số cũ thì callback của họ bị từ chối. Đúng lỗi đang vá, chỉ đổi hình dạng |
| Cho IPN chấp nhận nếu khớp **một trong hai** số | Nới điều kiện đối chiếu số tiền — chính là chốt chống giả mạo. Không đánh đổi an toàn lấy tiện lợi ở đúng chỗ này |

### Hệ quả

- Migration `0011_cartorder_vnpay_amount` thêm một cột nullable → `ADD COLUMN` thường
  trên PostgreSQL, **không backfill**. Đơn đang treo trên production mang `NULL` và đi
  vào nhánh dự phòng ở chốt 1, nên deploy không làm hỏng chúng.
- Nhánh dự phòng đó **bắt buộc phải có**. Bỏ đi là mọi đơn treo trước lúc deploy hỏng
  ngay — [core/test_vnpay_flow.py](../grocerly/core/test_vnpay_flow.py) có test riêng cho
  đúng điều đó, và nó đỏ khi thử bỏ nhánh.
- Khách bỏ dở ở cổng rồi quay lại vẫn **trả được** đơn đó, chỉ là trả theo giá đã khóa.
  Muốn giá khác thì đặt đơn mới.
- Báo cáo: UC 3.2.21 (áp mã giảm giá) cần thêm một tiền điều kiện *đơn chưa được chuyển
  sang cổng thanh toán* — cùng loại bổ sung với hai tiền điều kiện của UC 3.2.25 ở
  ADR-0007. Ghi ở [PLAN](PLAN.md) bước 3.26.

### Ghi chú cho báo cáo

Cặp S-12 / S-13 đáng để cạnh nhau trong mục rà soát bảo mật: cả hai đều **không phải lỗ
hổng cho người ngoài** — S-12 cần quyền quản trị viên, S-13 cần chính khách hàng tự làm
lệch đơn của mình. Nhưng hậu quả đi ngược chiều nhau: S-12 làm hệ thống **thu thiếu**,
S-13 làm hệ thống **không ghi nhận khoản đã thu**. Cái thứ hai tệ hơn cho khách hàng, và
là loại lỗi không ai báo cáo vì người gặp không biết mình đang gặp.
