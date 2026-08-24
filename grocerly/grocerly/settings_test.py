"""Settings dùng riêng cho việc chạy test.

`grocerly/.env` trỏ vào database production trên Neon, nên `manage.py test` với settings
mặc định sẽ tạo database `test_<tên-db>` **trên máy chủ production**. Module này ép dùng
SQLite in-memory để test hoàn toàn không đụng tới dữ liệu thật.

    python manage.py test --settings=grocerly.settings_test
"""

from grocerly.settings import *  # noqa: F401,F403

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
