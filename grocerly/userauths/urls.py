from django.urls import path
from userauths import views
from django.contrib.auth import views as auth_views

app_name = 'userauths'

urlpatterns = [
    path('sign-up/', views.register_view, name='sign-up'),
    path('sign-in/', views.login_view, name='sign-in'),
    path('sign-out/', views.logout_view, name='sign-out'),
    path('profile/update/', views.profile_update, name='profile-update'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='userauths/password-reset.html',
        success_url='/user/password-reset/done/',
        email_template_name='userauths/password_reset_email.html'
    ), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='userauths/password-reset-done.html'
    ), name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='userauths/password-reset-confirm.html',
        success_url='/user/password-reset-complete/'
    ), name='password_reset_confirm'),
    
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='userauths/password-reset-complete.html'
    ), name='password_reset_complete'),
]