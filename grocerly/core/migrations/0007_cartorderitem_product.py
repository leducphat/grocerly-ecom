"""Thêm khóa ngoại `Product` cho `CartOrderItem` — ADR-0006, PLAN bước 2.11.

Migration gồm hai phần: thêm cột, rồi **backfill** dữ liệu cũ.

Backfill chỉ có một manh mối duy nhất là `item` (tên sản phẩm chép lại lúc đặt hàng),
nên nó **cố tình không đoán bừa**: chỉ nối khi tên đó ứng với đúng **một** sản phẩm.
Trùng tên hai sản phẩm thì để `NULL` — nối sai một dòng hóa đơn về nhầm sản phẩm còn tệ
hơn là để trống, vì cái sai đó im lặng và sẽ được các bước sau tin là đúng.
"""

import django.db.models.deletion
from django.db import migrations, models


def link_existing_items_to_products(apps, schema_editor):
    CartOrderItem = apps.get_model('core', 'CartOrderItem')
    Product = apps.get_model('core', 'Product')

    # Manager của model lịch sử là `models.Manager` thuần (SoftDeleteManager không đặt
    # `use_in_migrations`), nên truy vấn này **có cả sản phẩm đã xóa mềm** — đúng ý:
    # một sản phẩm ngừng bán vẫn là sản phẩm khách đã mua.
    titles = set(
        CartOrderItem.objects.filter(product__isnull=True)
        .values_list('item', flat=True)
    )
    if not titles:
        return

    # Đếm số sản phẩm mang mỗi tên để loại các tên nhập nhằng.
    matches = {}
    for pk, title in Product.objects.filter(title__in=titles).values_list('id', 'title'):
        matches.setdefault(title, []).append(pk)

    unambiguous = {
        title: pks[0] for title, pks in matches.items() if len(pks) == 1
    }
    for title, product_id in unambiguous.items():
        CartOrderItem.objects.filter(product__isnull=True, item=title).update(
            product_id=product_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_drop_stripe_payment_intent'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartorderitem',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items', to='core.product'),
        ),
        # Chiều ngược lại là no-op: rollback sẽ drop luôn cột, không cần gỡ dữ liệu.
        migrations.RunPython(
            link_existing_items_to_products,
            migrations.RunPython.noop,
        ),
    ]
