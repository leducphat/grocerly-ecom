"""Giới hạn tần suất cho endpoint chatbot — SECURITY.md S-03.

`/api/v1/chat/` không bắt đăng nhập (khách vãng lai vẫn phải dùng được chatbot theo
UC 3.2.15), nên chốt chặn duy nhất là giới hạn theo IP / theo tài khoản. Mỗi lượt gọi
tiêu tốn hạn ngạch Gemini của chủ dự án — miễn phí 500 tin/ngày — nên không giới hạn
nghĩa là bất kỳ ai cũng làm chatbot ngừng hoạt động được.
"""

from django.utils.translation import gettext as _
from rest_framework.exceptions import Throttled
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import exception_handler


class ChatAnonThrottle(AnonRateThrottle):
    """Khách vãng lai — đếm theo địa chỉ IP."""
    scope = 'ai_chat_anon'


class ChatUserThrottle(UserRateThrottle):
    """Người đã đăng nhập — đếm theo tài khoản, rộng tay hơn khách vãng lai."""
    scope = 'ai_chat_user'


def chat_exception_handler(exc, context):
    """Trả lỗi 429 dưới dạng widget chat hiểu được.

    Widget ở base.html chỉ đọc `reply` và `error`; response mặc định của DRF là
    `{"detail": ...}` nên sẽ bị nuốt im lặng — người dùng gõ mà không thấy gì phản hồi.
    Giữ nguyên mã 429 (đúng ngữ nghĩa HTTP, còn thấy được khi xem log), chỉ đổi phần thân.
    """
    response = exception_handler(exc, context)

    if isinstance(exc, Throttled) and response is not None:
        wait_seconds = int(exc.wait or 0)
        response.data = {
            'reply': _(
                "⏳ Bạn đang nhắn quá nhanh. Vui lòng đợi khoảng %(wait_seconds)s giây rồi thử lại nhé!"
            ) % {'wait_seconds': wait_seconds},
            'retry_after': wait_seconds,
        }

    return response
