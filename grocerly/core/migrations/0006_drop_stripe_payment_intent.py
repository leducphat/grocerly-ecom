"""Bỏ cột `stripe_payment_intent` khỏi `CartOrder` — PLAN bước 2.4.

Đây **không phải quyết định mới**: field đã bị xóa khỏi `core/models.py` từ commit
`0925f27` nhưng chưa bao giờ có migration đi kèm, nên model và database lệch nhau suốt
từ đó. Migration này chỉ ghi nốt phần còn thiếu.

Cột là tàn dư của template Stripe ban đầu; dự án thanh toán bằng VNPay và COD, không
dùng Stripe (dependency đã gỡ ở commit `26b3b49`). Báo cáo cũng không có cột này ở ERD
Hình 45 lẫn Bảng 32 — xem SPEC-GAPS B11 — nên bỏ cột là làm code khớp báo cáo, không
phải ngược lại.

An toàn dữ liệu: đã kiểm production trước khi viết — 11 đơn hàng, **0 đơn có dữ liệu**
ở cột này. Cột `null=True` nên không có ràng buộc nào phụ thuộc vào nó.

Chiều lùi là no-op có chủ ý: khôi phục một cột luôn rỗng không mang lại gì, và
`RemoveField` của Django vốn đã tự đảo được nếu thật sự cần.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_product_status_drop_review_flow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartorder',
            name='stripe_payment_intent',
        ),
    ]
