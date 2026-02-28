from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Homepage
    path('', views.index, name='index'),
    path('products/', views.product_list_view, name='product-list'),
    path('products/<p_id>/', views.product_detail_view, name='product-detail'),

    # Category
    path('categories/', views.category_list_view, name='category-list'),
    path('categories/<c_id>/', views.category_product_list_view, name='category-product-list'),

    # Vendor
    path('vendors/', views.vendor_list_view, name='vendor-list'),
    path('vendors/<v_id>/', views.vendor_detail_view, name='vendor-detail'),

    # Tags
    path('products/tag/<slug:tag_slug>/', views.tag_list, name='tags'),

    # Add Review (AJAX)
    path('ajax-add-review/<int:p_id>/', views.ajax_add_review, name='ajax-add-review'),

    # Search
    path('search/', views.search_view, name='search'),

    # Cart
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('cart/', views.cart_view, name='cart'),
    path('delete-from-cart/', views.delete_item_from_cart, name='delete-from-cart'),
    path('update-cart/', views.update_cart, name='update-cart'),

    # Checkout + Payment
    path('save-checkout-info/', views.save_checkout_info, name='save_checkout_info'),
    path('api/create-checkout-session/<oid>/', views.create_checkout_session, name='api_checkout_session'),
    path('checkout/<oid>/', views.checkout, name='checkout'),
    path('payment-completed/<oid>/', views.payment_completed_view, name='payment-completed'),
    path('payment-failed/', views.payment_failed_view, name='payment-failed'),

    # Dashboard
    path('dashboard/', views.customer_dashboard, name='dashboard'),
    path('dashboard/order/<int:id>/', views.order_detail, name='order-detail'),

    # Address
    path('make-default-address/', views.make_address_default, name='make-default-address'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('add-to-wishlist/', views.add_to_wishlist, name='add-to-wishlist'),
    path('remove-from-wishlist/', views.remove_wishlist, name='remove-from-wishlist'),
]