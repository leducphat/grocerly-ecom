# AGENTS.md

Chỉ dẫn cho AI coding agent làm việc trong repo **Grocerly**.
Đây là **nguồn duy nhất** — `CLAUDE.md` và `.github/copilot-instructions.md` đều trỏ về file này.

## Dự án là gì

Grocerly là website thương mại điện tử bán thực phẩm/tạp hóa, có tích hợp trợ lý AI
(Google Gemini) giúp khách tìm sản phẩm và đặt hàng bằng hội thoại.

Đây là **tiểu luận chuyên ngành Công nghệ phần mềm** (HCMUTE) — không phải sản phẩm
thương mại. Điều đó ảnh hưởng tới cách ưu tiên công việc: **độ khớp giữa code và bản
báo cáo đặc tả quan trọng ngang với chất lượng code**. Xem [docs/SPEC-GAPS.md](docs/SPEC-GAPS.md).

Mô hình nghiệp vụ: **một siêu thị, nhiều nhân viên** (kiểu Bách Hóa Xanh / Co.opmart),
**không phải sàn nhiều người bán** kiểu Shopee. Xem ADR-0003 trong
[docs/DECISIONS.md](docs/DECISIONS.md).

## Lệnh thường dùng

> ⚠️ Mã nguồn nằm trong thư mục con `grocerly/`, **không** phải ở gốc repo.
> Mọi lệnh `manage.py` phải chạy từ `grocerly/`.

⚠️ **Chạy dev server ở local phải dùng `--settings=grocerly.settings_local`:**

```bash
cd grocerly
python manage.py migrate   --settings=grocerly.settings_local   # lần đầu
python manage.py runserver --settings=grocerly.settings_local
```

`runserver` với settings mặc định đọc **và ghi** thẳng vào Neon production (bẫy #5).
Thử luồng "Lưu nháp / Đăng bán / Ngừng bán" mà quên đổi settings là sửa sản phẩm thật.
`settings_local` ép SQLite (`db.sqlite3`) và tắt Cloudinary. Cả hai đã gitignore.

```bash
cd grocerly

python manage.py runserver          # ⚠️ DB PRODUCTION — xem cảnh báo trên
python manage.py makemigrations     # sinh migration
python manage.py migrate            # áp migration
python manage.py createsuperuser    # tạo tài khoản Admin
python manage.py collectstatic      # gom static (cần trước khi deploy)
python manage.py compilemessages    # biên dịch .po -> .mo sau khi sửa bản dịch
python manage.py makemessages -l vi # trích chuỗi cần dịch
```

```bash
# Test phải chạy với settings riêng — xem cảnh báo bên dưới
python manage.py test core --settings=grocerly.settings_test
```

⚠️ **Luôn dùng `--settings=grocerly.settings_test` khi chạy test.** Với settings mặc định,
`manage.py test` sẽ tạo database `test_<tên-db>` **trên máy chủ production Neon** (bẫy #5).
Module này ép SQLite in-memory.

Hiện chỉ [core/tests.py](grocerly/core/tests.py) có test (12 test hồi quy cho các lỗ hổng
đã vá ở [docs/SECURITY.md](docs/SECURITY.md)). `userauths`, `useradmin`, `store_api` vẫn là
stub rỗng — các luồng đó kiểm thử thủ công theo kịch bản hộp đen ở chương 4 báo cáo.

## Ngăn xếp công nghệ

| Lớp | Công nghệ |
|---|---|
| Backend | Python 3.12 (Docker) / 3.10+ (local), Django 5.2.4 — kiến trúc MVT, toàn function-based view |
| API | Django REST Framework 3.15 — chỉ dùng cho `/api/v1/` phục vụ chatbot |
| CSDL | PostgreSQL (Neon serverless); tự fallback SQLite nếu thiếu biến môi trường |
| AI | `google-generativeai` 0.8.3, model `gemini-3.1-flash-lite`, function calling thủ công |
| Thanh toán | VNPay (tự implement HMAC-SHA512) + COD |
| Media | Cloudinary (production) / FileSystemStorage (local); static qua WhiteNoise |
| Frontend | Django template + Bootstrap + jQuery AJAX (không có build step, không SPA) |
| Admin | django-jazzmin |
| Triển khai | Render (`build.sh`); có sẵn Dockerfile + nginx + script EC2 nhưng không dùng chính |

## Cấu trúc

```
grocerly-ecom/
├── AGENTS.md, CLAUDE.md          # chỉ dẫn cho AI agent
├── docs/                          # tài liệu kỹ thuật (xem cuối file)
└── grocerly/                      # ROOT của Django project
    ├── manage.py
    ├── .env                       # ⚠️ trỏ vào DB PRODUCTION — đã gitignore
    ├── grocerly/                  # settings, urls, wsgi, middleware
    ├── core/                      # catalog, giỏ hàng, checkout, VNPay, wishlist, review
    ├── userauths/                 # User (login bằng email), Profile, ContactUs
    ├── useradmin/                 # dashboard cho Nhân viên (staff)
    ├── store_api/                 # DRF endpoints + trợ lý AI Gemini
    ├── templates/                 # ~62 template
    ├── static/                    # asset tĩnh (đã build sẵn, có cả SCSS nguồn)
    └── locale/{vi,en}/            # bản dịch i18n
```

Chi tiết kiến trúc và luồng xử lý: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quy ước code

- **View**: function-based view. Không dùng CBV trừ view auth sẵn có của Django.
- **Định danh trên URL**: dùng ShortUUID (`p_id`, `c_id`, `v_id`, `oid`), **không** dùng khóa chính số.
- **i18n**: mọi chuỗi hiển thị phải bọc `{% trans %}` hoặc `gettext_lazy as _`. Mặc định tiếng Việt.
- **Tiền tệ**: hiển thị qua filter `{{ value|vnd }}` (`core/templatetags/currency_filters.py`).
- **Xóa dữ liệu**: model quan trọng kế thừa `SoftDeleteModel` — xem mục Bẫy bên dưới.
- **Commit**: Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`).
  Message tiếng Anh, thân message giải thích *tại sao*.
- **Nhánh**: làm việc trên `develop`, `main` là nhánh phát hành.

## ⚠️ Bẫy đã biết — đọc trước khi sửa code

1. **Hai field trùng tên `product_status`, khác ý nghĩa hoàn toàn:**
   - `Product.product_status` → trạng thái đăng bán (`draft`/`published`/`disabled`)
   - `CartOrder.product_status` / `CartOrderItem.product_status` → trạng thái giao hàng
     (`processing`/`shipped`/`delivered`)

   **Không bao giờ tìm-thay-thế toàn cục trên chuỗi `product_status`.**

2. **`Product` có ba cờ trạng thái chồng chéo**: `product_status` (workflow),
   `status` (bool), `in_stock` (bool). Storefront lọc theo `product_status='published'`,
   nhưng `store_api` lại lọc theo `status=True, in_stock=True` → **không nhất quán**,
   đang là lỗi mở (xem [docs/SECURITY.md](docs/SECURITY.md) mục S-04).

3. **Soft delete không áp dụng cho instance**: `SoftDeleteModel` chỉ override `delete()`
   ở tầng *QuerySet*. Gọi `product.delete()` trên một object vẫn **xóa vĩnh viễn**.
   Muốn xóa mềm phải gọi `product.soft_delete()`.
   Dùng `Model.objects` để lấy bản ghi còn sống, `Model.all_objects` để lấy tất cả.

4. **`core.models.Tag` là model rỗng không dùng** (`class Tag(models.Model): pass`).
   Tag thật do `django-taggit` quản lý ở bảng riêng. Đừng nhầm.

5. **`grocerly/.env` trỏ thẳng vào database production trên Neon.** Chạy `migrate`,
   `flush`, hay shell ghi dữ liệu ở local sẽ tác động lên dữ liệu thật. Luôn xác nhận
   với người dùng trước khi chạy lệnh ghi.

6. **`RestrictStaffMiddleware` chặn staff/superuser vào storefront** và đá về trang quản
   trị. Khi test luồng khách hàng phải dùng tài khoản không phải staff.

7. **Giỏ hàng lưu trong session** (`request.session['cart_data_obj']`), không có model Cart.
   Sau khi sửa dict phải gán lại vào session hoặc set `request.session.modified = True`.

8. **URL có tiền tố ngôn ngữ** (`/vi/...`, `/en/...`) do `i18n_patterns`, trừ `/api/v1/`
   được đặt ngoài. Hardcode URL không tiền tố sẽ 404.

## Trước khi báo hoàn thành

- [ ] Đã chạy `python manage.py check` không lỗi
- [ ] Đã chạy `python manage.py test core --settings=grocerly.settings_test` không đỏ
- [ ] Nếu sửa model: đã tạo migration và giải thích ảnh hưởng tới dữ liệu hiện có
- [ ] Nếu thêm chuỗi hiển thị: đã bọc i18n và cập nhật `locale/vi/LC_MESSAGES/django.po`
- [ ] Nếu sửa chức năng có trong báo cáo: đã ghi chú cần cập nhật mục nào
      ([docs/SPEC-GAPS.md](docs/SPEC-GAPS.md))
- [ ] Không hardcode secret; không commit `.env`
- [ ] Không thêm `console.log` / `print` debug còn sót

## Nguyên tắc làm việc với repo này

- **Kiểm chứng trước khi khẳng định.** Bản báo cáo đặc tả nhiều chức năng chưa được cài
  đặt. Trước khi nói "chức năng X đã có", hãy `grep` trong code.
- **Đề xuất thay đổi tối thiểu.** Đây là đồ án sắp bảo vệ, không phải refactor lớn.
- **Nêu ảnh hưởng tới báo cáo.** Mỗi thay đổi code có thể làm lệch use case / sequence
  diagram — hãy chỉ rõ mục nào cần sửa theo.

## Tài liệu

| File | Nội dung |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Kiến trúc hệ thống, mô hình dữ liệu, các luồng chính |
| [docs/PLAN.md](docs/PLAN.md) | Kế hoạch công việc đang triển khai và backlog ưu tiên |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Nhật ký quyết định kiến trúc (ADR) |
| [docs/SPEC-GAPS.md](docs/SPEC-GAPS.md) | Khoảng cách giữa báo cáo và code thực tế |
| [docs/SECURITY.md](docs/SECURITY.md) | Lỗ hổng đã phát hiện, mức độ và hướng khắc phục |
