"""Bỏ quy trình duyệt sản phẩm — ADR-0002.

`STATUS` rút từ 5 giá trị xuống 3 (`draft` / `published` / `disabled`) và mặc định đổi
từ `in_review` sang `draft`. Dữ liệu cũ được chuyển sang trạng thái *ẩn tương đương* để
không sản phẩm nào tự lên sàn sau khi migrate:

    in_review → draft       (đang chờ duyệt → nháp, nhân viên tự bấm Đăng bán)
    rejected  → disabled    (bị từ chối → ngừng bán)

Sản phẩm đang `published` / `draft` / `disabled` **không bị đụng tới**.
"""

from django.db import migrations, models


# Không dùng dict comprehension ngược được: hai giá trị cũ gộp vào các trạng thái đã tồn
# tại từ trước, nên không phân biệt được bản ghi nào vốn là 'draft' và bản ghi nào từ
# 'in_review' chuyển sang. Vì vậy chiều lùi là no-op có chủ ý.
STATUS_MAP = {
    'in_review': 'draft',
    'rejected': 'disabled',
}


def forwards(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    for old_status, new_status in STATUS_MAP.items():
        # Manager của model lịch sử là Manager thường, không lọc soft-delete —
        # đúng ý: sản phẩm đã xóa mềm cũng phải đổi để không kẹt giá trị không hợp lệ.
        Product.objects.filter(product_status=old_status).update(product_status=new_status)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_product_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_status',
            field=models.CharField(
                choices=[('draft', 'Draft'), ('published', 'Published'), ('disabled', 'Disabled')],
                default='draft',
                max_length=10,
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
