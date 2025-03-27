from django.urls import path

from . import views

urlpatterns = [
    path(
        'profile/<str:username>/',
        views.UserProfileView.as_view(),
        name='user_profile'
    ),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path(
        'create/',
        views.UserFormCreateView.as_view(),
        name='user_create'
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
        views.UserFormDeleteView.as_view(),
        name='user_delete'
    ),
]
