from django.urls import path
from userauths import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from django.urls import reverse_lazy

app_name = 'userauths'

urlpatterns = [
    path('sign-up/', views.register_view, name='sign-up'),
    path('sign-in/', views.login_view, name='sign-in'),
    path('sign-out/', views.logout_view, name='sign-out'),
    path('profile/update/', views.profile_update, name='profile-update'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='userauths/password-reset.html',
        success_url=reverse_lazy('userauths:password_reset_done'),
        email_template_name='userauths/password_reset_email.html'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='userauths/password-reset-done.html'
    ), name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='userauths/password-reset-confirm.html',
        success_url=reverse_lazy('userauths:password_reset_complete')
    ), name='password_reset_confirm'),
    
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='userauths/password-reset-complete.html'
    ), name='password_reset_complete'),

    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='userauths/password-change.html',
        success_url=reverse_lazy('userauths:password_change_done')
    ), name='password_change'),
    
    path('change-password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='userauths/password-change-done.html'
    ), name='password_change_done'),

    # URL dùng để xem nhanh UI (không cần logic token/email)
    path('test-ui/password-reset/', TemplateView.as_view(template_name='userauths/password-reset.html')),
    path('test-ui/password-reset-done/', TemplateView.as_view(template_name='userauths/password-reset-done.html')),
    path('test-ui/password-reset-confirm/', TemplateView.as_view(template_name='userauths/password-reset-confirm.html')),
    path('test-ui/password-reset-complete/', TemplateView.as_view(template_name='userauths/password-reset-complete.html')),
]