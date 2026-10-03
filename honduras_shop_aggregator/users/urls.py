from django.urls import path

from . import views

urlpatterns = [
    path(
        'profile/<str:username>/',
        views.UserProfileView.as_view(),
        name='user_profile'
    ),
    path('anonymous/', views.AnonymousProfileView.as_view(), name='anonymous_profile'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path(
        'create/',
        views.UserFormCreateView.as_view(),
        name='user_create'
    ),
    path(
        'email-verification/',
        views.EmailVerificationSentView.as_view(),
        name='email_verification_sent'
    ),
    path(
        'email-verification/resend/',
        views.EmailVerificationResendView.as_view(),
        name='email_verification_resend'
    ),
    path(
        'email-verification/<uidb64>/<token>/',
        views.EmailVerificationConfirmView.as_view(),
        name='email_verification_confirm'
    ),
    path(
        '<str:username>/update/',
        views.UserFormUpdateView.as_view(),
        name='user_update'
    ),
    path(
        '<str:username>/password_change/',
        views.UserPasswordChangeView.as_view(),
        name='user_password_change'
    ),
    path(
        '<str:username>/delete/',
        views.UserSoftDeleteView.as_view(),
        name='user_delete'
    ),
]
