from django.urls import path

from . import views

urlpatterns = [
    path(
        'profile/<str:store_name>/',
        views.SellerProfileView.as_view(),
        name='seller_profile'
    ),
    path(
        'create/',
        views.SellerFormCreateView.as_view(),
        name='seller_create'
    ),
    # path(
    #     '<str:username>/update/',
    #     views.UserFormUpdateView.as_view(),
    #     name='user_update'
    # ),
    # path(
    #     '<str:username>/delete/',
    #     views.UserFormDeleteView.as_view(),
    #     name='user_delete'
    # ),
]
