"""Settings để chạy dev server ở máy local.

`grocerly/.env` trỏ vào database production trên Neon, nên `runserver` với settings mặc
định sẽ đọc — và ghi — thẳng vào dữ liệu thật (bẫy #5 trong AGENTS.md). Thử luồng
"Lưu nháp / Đăng bán / Ngừng bán" mà quên đổi settings là sửa sản phẩm thật của site.

Module này ép SQLite ở đĩa local và tắt Cloudinary để ảnh upload không đẩy lên tài khoản
media của production.

    python manage.py migrate    --settings=grocerly.settings_local
    python manage.py runserver  --settings=grocerly.settings_local

`db.sqlite3` và `media/` đều đã nằm trong .gitignore.
"""

import os

# Xem ghi chú cùng nội dung trong `settings_test.py`: `settings.py` nay từ chối khởi
# động khi `DEBUG=False` mà thiếu `DJANGO_SECRET_KEY`.
os.environ.setdefault('DJANGO_SECRET_KEY', 'insecure-key-for-local-development-only')

from grocerly.settings import *  # noqa: E402,F401,F403

DEBUG = True

# `DEBUG` ở trên được gán SAU khi `settings.py` đã tính hai cờ này, nên phải đặt lại tay.
# Bỏ qua là dev server local chạy trên http:// mất sạch cookie — đăng nhập không vào được
# mà không có thông báo lỗi nào.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # noqa: F405
    }
}

# Ảnh upload nằm ở đĩa local, không đụng tới Cloudinary của production.
USE_CLOUDINARY = False
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # noqa: F405
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # StaticFilesStorage thay cho WhiteNoise nén: không cần collectstatic trước khi chạy.
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
