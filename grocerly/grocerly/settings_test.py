"""Settings dùng riêng cho việc chạy test.

`grocerly/.env` trỏ vào database production trên Neon, nên `manage.py test` với settings
mặc định sẽ tạo database `test_<tên-db>` **trên máy chủ production**. Module này ép dùng
SQLite in-memory để test hoàn toàn không đụng tới dữ liệu thật.

    python manage.py test --settings=grocerly.settings_test
"""

import os

# Đặt TRƯỚC khi import settings: từ 2026-08-26 `settings.py` từ chối khởi động nếu
# `DEBUG=False` mà thiếu `DJANGO_SECRET_KEY` ([S-05](../../docs/SECURITY.md)). Không có
# dòng này thì một bản clone mới — chưa có `.env` — không chạy nổi `manage.py test`.
# `setdefault` nên `.env` của máy đang làm việc vẫn thắng.
os.environ.setdefault('DJANGO_SECRET_KEY', 'insecure-key-for-the-test-suite-only')

from grocerly.settings import *  # noqa: E402,F401,F403

# Đặt tay chứ không để suy ra từ `DEBUG`: giá trị đó phụ thuộc `.env` của từng máy, mà
# test phải cho cùng kết quả ở mọi máy. `manage.py test` chạy trên `http://testserver`
# nên cookie có cờ `Secure` sẽ không bao giờ được gửi đi.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Ảnh không cần đẩy lên Cloudinary khi chạy test.
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Hash nhanh cho test, không dùng ở nơi khác.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
