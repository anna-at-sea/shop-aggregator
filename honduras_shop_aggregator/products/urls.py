from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.ProductListView.as_view(),
        name='product_list'
    ),
    path(
        'create/',
        views.ProductFormCreateView.as_view(),
        name='product_create'
    ),
    path(
        '<str:slug>/update_image/',
        views.ProductFormUpdateImageView.as_view(),
        name='product_update_image'
    ),
    path(
        '<str:slug>/',
        views.ProductCardView.as_view(),
        name='product_card'
    ),
    # path(
    #     '<str:store_name>/update/',
    #     views.SellerFormUpdateView.as_view(),
    #     name='seller_update'
    # ),
    # path(
    #     '<str:store_name>/delete/',
    #     views.SellerFormDeleteView.as_view(),
    #     name='seller_delete'
    # ),
]
