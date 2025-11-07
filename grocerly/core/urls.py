from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Homepage
    path('', views.index, name='index'),
    path('products/', views.product_list_view, name='product-list'),

    # Category
    path('categories/', views.category_list_view, name='category-list'),
    path('categories/<c_id>/', views.category_product_list_view, name='category-product-list'),

    # Vendor
    path('vendors/', views.vendor_list_view, name='vendor-list'),
]