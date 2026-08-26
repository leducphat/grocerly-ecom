"""Backfill của migration `0007_cartorderitem_product` — PLAN bước 2.11, ADR-0006.

Migration này không chỉ thêm cột: nó còn **nối dữ liệu cũ** về sản phẩm gốc bằng manh
mối duy nhất còn lại là tên (`CartOrderItem.item`). Nó sẽ chạy một lần trên database
production ở Neon, nên hành vi của nó cần được chốt lại chứ không chỉ đọc bằng mắt.

Điểm cần chứng minh không phải là "nối được", mà là **nó biết lúc nào KHÔNG nên nối**:
tên trùng hai sản phẩm thì để `NULL` chứ không chọn bừa một cái. Nối sai một dòng hóa
đơn về nhầm sản phẩm là cái sai im lặng, và các bước sau sẽ tin nó là đúng.

Test dùng `MigrationExecutor` để chạy migration thật trên schema thật, thay vì gọi hàm
backfill với model hiện tại — model lịch sử ở trạng thái 0006 **chưa có** cột `product`,
và đó chính là điều kiện cần tái hiện.
"""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class BackfillProductLinkTests(TransactionTestCase):

    migrate_from = [('core', '0006_drop_stripe_payment_intent')]
    migrate_to = [('core', '0007_cartorderitem_product')]

    def _state_at(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def setUp(self):
        # Lùi schema về trước khi có cột `product`.
        self.old_apps = self._state_at(self.migrate_from)

    def tearDown(self):
        # Trả database về trạng thái mới nhất cho các test khác.
        self._state_at(self.migrate_to)

    def _make_order_line(self, item_title):
        CartOrder = self.old_apps.get_model('core', 'CartOrder')
        CartOrderItem = self.old_apps.get_model('core', 'CartOrderItem')
        order = CartOrder.objects.create(price=0)
        return CartOrderItem.objects.create(
            order=order,
            invoice_no=f"INVOICE_NO-{order.id}",
            item=item_title,
            image="/media/products.jpg",
            quantity=1,
            price=0,
            total=0,
        ).id

    def _make_product(self, title, **kwargs):
        Product = self.old_apps.get_model('core', 'Product')
        return Product.objects.create(title=title, **kwargs).id

    def _line_after_migration(self, line_id):
        new_apps = self._state_at(self.migrate_to)
        return new_apps.get_model('core', 'CartOrderItem').objects.get(id=line_id)

    def test_a_line_is_linked_when_exactly_one_product_carries_that_name(self):
        product_id = self._make_product("Dưa hấu")
        line_id = self._make_order_line("Dưa hấu")

        self.assertEqual(self._line_after_migration(line_id).product_id, product_id)

    def test_an_ambiguous_name_is_left_unlinked_rather_than_guessed(self):
        """Hai sản phẩm cùng tên → không có cách nào biết khách mua cái nào."""
        self._make_product("Dưa hấu")
        self._make_product("Dưa hấu")
        line_id = self._make_order_line("Dưa hấu")

        self.assertIsNone(self._line_after_migration(line_id).product_id)

    def test_a_name_that_matches_nothing_is_left_unlinked(self):
        """Sản phẩm đã bị xóa cứng khỏi database từ lâu — không còn gì để nối tới."""
        self._make_product("Xoài cát")
        line_id = self._make_order_line("Sản phẩm đã bị xóa")

        self.assertIsNone(self._line_after_migration(line_id).product_id)

    def test_a_soft_deleted_product_still_gets_linked(self):
        """Ngừng bán không phải là chưa từng bán.

        Model lịch sử trong migration dùng manager thuần nên `objects` **không** lọc bỏ
        bản ghi xóa mềm. Test này chốt lại điều đó — nếu ai đó đổi `SoftDeleteManager`
        thành `use_in_migrations = True`, backfill sẽ âm thầm bỏ sót nhóm này.
        """
        product_id = self._make_product("Dưa hấu", is_deleted=True)
        line_id = self._make_order_line("Dưa hấu")

        self.assertEqual(self._line_after_migration(line_id).product_id, product_id)

    def test_each_line_keeps_its_own_name(self):
        """Nhiều dòng, nhiều tên — không được nối chéo sang nhau."""
        watermelon_id = self._make_product("Dưa hấu")
        mango_id = self._make_product("Xoài cát")
        watermelon_line = self._make_order_line("Dưa hấu")
        mango_line = self._make_order_line("Xoài cát")

        self.assertEqual(self._line_after_migration(watermelon_line).product_id, watermelon_id)
        self.assertEqual(self._line_after_migration(mango_line).product_id, mango_id)

    def test_the_static_snapshot_is_not_touched(self):
        """Backfill chỉ ghi vào cột `product`, không được sửa bản sao tĩnh của hóa đơn."""
        self._make_product("Dưa hấu")
        line_id = self._make_order_line("Dưa hấu")

        line = self._line_after_migration(line_id)
        self.assertEqual(line.item, "Dưa hấu")
        self.assertEqual(line.quantity, 1)
