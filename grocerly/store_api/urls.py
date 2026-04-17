from django.urls import path
from . import views

app_name = 'store_api'

urlpatterns = [
    path('products/', views.ProductListAPI.as_view(), name='api-products'),
    path('categories/', views.CategoryListAPI.as_view(), name='api-categories'),
    path('chat/', views.ai_chat, name='api-chat'),
]
