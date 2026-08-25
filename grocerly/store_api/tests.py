"""Kiểm thử rò rỉ hàng nháp qua API công khai và chatbot — SECURITY.md S-04.

Tương ứng bước 5.2 trong docs/PLAN.md.
"""

import json
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase

from core.models import Product
from store_api.views import (
    MAX_HISTORY_TURNS, MAX_MESSAGE_LENGTH, get_bestsellers, search_products,
)
from store_api.throttling import ChatAnonThrottle, ChatUserThrottle
from userauths.models import User


class DraftLeakTests(TestCase):

    def setUp(self):
        self.published = Product.objects.create(
            title="Dưa hấu đỏ", product_status='published', featured=True,
        )
        self.draft = Product.objects.create(
            title="Dưa hấu vàng", product_status='draft', featured=True,
        )
        self.disabled = Product.objects.create(
            title="Dưa hấu xanh", product_status='disabled', featured=True,
        )

    def test_product_list_api_hides_unpublished(self):
        response = self.client.get("/api/v1/products/")

        titles = [item['title'] for item in response.json()]
        self.assertEqual(titles, ["Dưa hấu đỏ"])

    def test_chatbot_search_hides_unpublished(self):
        results = search_products("Dưa hấu")

        titles = [item.get('title') for item in results]
        self.assertEqual(titles, ["Dưa hấu đỏ"])

    def test_chatbot_bestsellers_hide_unpublished(self):
        results = get_bestsellers()

        titles = [item['title'] for item in results]
        self.assertEqual(titles, ["Dưa hấu đỏ"])


class ChatThrottleTests(TestCase):
    """SECURITY.md S-03 — endpoint chatbot phải có giới hạn tần suất."""

    # `override_settings(REST_FRAMEWORK=...)` KHÔNG đổi được rate: DRF gán
    # `SimpleRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES` ngay lúc
    # import, nên reload settings tạo dict mới còn throttle vẫn giữ dict cũ. Ghi đè thẳng
    # thuộc tính `rate` của class thì `__init__` bỏ qua `get_rate()` và dùng luôn.
    ANON_RATE = '3/min'
    USER_RATE = '10/min'

    def setUp(self):
        # Bộ đếm throttle nằm ở cache; không xóa thì các test ăn số của nhau.
        cache.clear()
        self.url = "/api/v1/chat/"

        for throttle_class, rate in [(ChatAnonThrottle, self.ANON_RATE),
                                     (ChatUserThrottle, self.USER_RATE)]:
            patcher = patch.object(throttle_class, 'rate', rate, create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

        # `model=None` khiến view trả lời ngay và **không gọi Gemini thật**.
        # Throttle được kiểm ở APIView.initial(), tức là trước thân view, nên vẫn đo được.
        no_model = patch("store_api.views.model", None)
        no_model.start()
        self.addCleanup(no_model.stop)

    def _send(self):
        return self.client.post(
            self.url, data=json.dumps({'message': "xin chào"}),
            content_type="application/json",
        )

    def test_anonymous_is_throttled_after_the_limit(self):
        for _i in range(3):
            self.assertEqual(self._send().status_code, 200)

        self.assertEqual(self._send().status_code, 429)

    def test_throttled_response_is_readable_by_the_chat_widget(self):
        for _i in range(4):
            response = self._send()

        # Widget ở base.html chỉ đọc `reply`/`error`; `detail` mặc định của DRF bị nuốt.
        self.assertEqual(response.status_code, 429)
        self.assertIn('reply', response.json())
        self.assertIn('retry_after', response.json())

    def test_logged_in_user_gets_a_higher_limit(self):
        user = User.objects.create_user(
            username="khach", email="khach@example.com", password="matkhau-kho-doan",
        )
        self.client.force_login(user)

        for _i in range(4):
            response = self._send()

        self.assertEqual(response.status_code, 200)


class ChatInputLimitTests(TestCase):
    """SECURITY.md S-03 — giới hạn độ dài tin nhắn và số lượt lịch sử."""

    def setUp(self):
        cache.clear()
        self.url = "/api/v1/chat/"
        self.model = MagicMock()
        self.model.start_chat.return_value.send_message.return_value.parts = []
        self.model.start_chat.return_value.send_message.return_value.text = "ok"
        patcher = patch("store_api.views.model", self.model)
        patcher.start()
        self.addCleanup(patcher.stop)
        key_patcher = patch("store_api.views.api_key", "test-key")
        key_patcher.start()
        self.addCleanup(key_patcher.stop)

    def _send(self, payload):
        return self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json",
        )

    def test_rejects_empty_message(self):
        self.assertEqual(self._send({'message': "   "}).status_code, 400)

    def test_rejects_non_string_message(self):
        self.assertEqual(self._send({'message': {'a': 1}}).status_code, 400)

    def test_rejects_overlong_message(self):
        response = self._send({'message': "a" * (MAX_MESSAGE_LENGTH + 1)})

        self.assertEqual(response.status_code, 400)
        self.model.start_chat.assert_not_called()

    def test_truncates_history_to_the_last_turns(self):
        history = [{'role': 'user', 'content': "tin %d" % i} for i in range(50)]

        self._send({'message': "xin chào", 'history': history})

        sent = self.model.start_chat.call_args.kwargs['history']
        self.assertEqual(len(sent), MAX_HISTORY_TURNS)
        self.assertEqual(sent[-1]['parts'], ["tin 49"])

    def test_ignores_history_that_is_not_a_list(self):
        self._send({'message': "xin chào", 'history': "khong-phai-list"})

        self.assertEqual(self.model.start_chat.call_args.kwargs['history'], [])
