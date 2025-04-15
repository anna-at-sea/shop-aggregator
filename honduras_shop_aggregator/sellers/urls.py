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
    path(
        '<str:store_name>/update/',
        views.SellerFormUpdateView.as_view(),
        name='seller_update'
    ),
    path(
        '<str:store_name>/delete/',
        views.SellerFormDeleteView.as_view(),
        name='seller_delete'
    ),
]
