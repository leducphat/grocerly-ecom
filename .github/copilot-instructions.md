# Grocerly AI Coding Guide

## Overview
- Django 5.2 project with two apps: core (catalog, vendors, orders) and userauths (custom user auth). Jazzmin skins the admin; ShortUUID provides human-friendly ids.
- SQLite is the default DB (grocerly/db.sqlite3). Media and static assets live under grocerly/media and grocerly/static; DEBUG serving is enabled in settings.

## App structure
- URLs: project routes in [grocerly/grocerly/urls.py](../grocerly/grocerly/urls.py); core routes for catalog/vendor pages in [grocerly/core/urls.py](../grocerly/core/urls.py); auth routes in [grocerly/userauths/urls.py](../grocerly/userauths/urls.py).
- Templates sit in [grocerly/templates](../grocerly/templates) with app-specific folders (core/, userauths/) and a shared base at [grocerly/templates/partials/base.html](../grocerly/templates/partials/base.html).
- Static assets are under [grocerly/static/assets](../grocerly/static/assets); SCSS sources exist in static/assets/scss and sass but are checked in compiled form too.

## Data model highlights (see [grocerly/core/models.py](../grocerly/core/models.py))
- `Category`, `Vendor`, `Product` use ShortUUID ids (`c_id`, `v_id`, `p_id`/`sku`). Image fields upload to `category/`, `products/`, and per-user dirs via `user_directory_path`.
- `Product.product_status` uses STATUS choices (`draft|disabled|in_review|rejected|published`); views filter on `published`. `featured` flag drives homepage.
- Orders: `CartOrder` and `CartOrderItem` track user carts with `STATUS_CHOICES` for fulfillment; `order_image()` builds media URLs.
- Social/storefront: `ProductReview` (rating 1–5), `Wishlist`, and `Address` tie back to the custom user.

## Views and routing (see [grocerly/core/views.py](../grocerly/core/views.py))
- Public pages are function-based views rendering templates directly; no DRF or CBVs.
- `index` shows featured + published products; `product_list_view` shows all published products; category/vendor detail pages fetch by ShortUUID (`c_id`, `v_id`).
- Queries are simple `.filter(...).order_by('-id')`; be mindful of N+1 if extending (eager-load related vendor/category when adding lists).

## Auth (see [grocerly/userauths/models.py](../grocerly/userauths/models.py) and [grocerly/userauths/views.py](../grocerly/userauths/views.py))
- Custom user model swaps username for email login (`AUTH_USER_MODEL = 'userauths.User'`, USERNAME_FIELD=email). Always reference via `settings.AUTH_USER_MODEL` or get_user_model.
- Registration uses `UserRegisterForm` (Django `UserCreationForm` subclass) capturing email/username; login view currently imports `django.contrib.auth.models.User` instead of the custom model—prefer the custom model for new work.
- Messaging framework is used for auth feedback; redirects land on `core:index` after login/register, and `userauths:sign-in` after logout.

## Context and templating
- Global context processor [grocerly/core/context_processors.py](../grocerly/core/context_processors.py) injects `categories` into all templates; avoid duplicating category queries in views.
- Templates expect `products`, `categories`, `vendors`, `vendor`, and `category` variables from views; mirror these names when adding pages.

## Developer workflow
- From the grocerly/ directory: `python manage.py runserver` to start; `python manage.py migrate` for schema; `python manage.py createsuperuser` to enter admin (Jazzmin skin).
- Media/fixtures: sample uploads live under grocerly/media (user_x/, category/, products/); ensure MEDIA_ROOT exists when running locally.
- Dependencies (no requirements.txt yet): install `django==5.2.4`, `shortuuid`, `django-jazzmin` in your venv.

## Conventions and pitfalls
- Use ShortUUID identifiers in URLs and lookups (`c_id`, `v_id`, `p_id`) instead of numeric PKs.
- Price fields use large `DecimalField` sizes with `decimal_places=3`; preserve when migrating.
- When adding new models, remember admin/Jazzmin display helpers often return HTML via `mark_safe` (see `category_image`, `vendor_image`, `product_image`).
- Keep new context processors lightweight; they run on every request.
- Prefer function-based views for consistency unless a new pattern is introduced intentionally.
