from django.urls import path

from . import views

urlpatterns = [
    path(
        'profile/<str:username>/',
        views.UserProfileView.as_view(),
        name='user_profile'
    ),
    path('login/', views.UserLoginView.as_view(), name='login'),
    # path(
    #     'create/',
    #     views.UserFormCreateView.as_view(),
    #     name='user_create'
    # ),
    # path(
    #     '<int:pk>/update/',
    #     views.UserFormUpdateView.as_view(),
    #     name='user_update'
    # ),
    # path(
    #     '<int:pk>/delete/',
    #     views.UserFormDeleteView.as_view(),
    #     name='user_delete'
    # ),
]
