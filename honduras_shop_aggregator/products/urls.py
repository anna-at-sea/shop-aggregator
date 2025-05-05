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
        '<str:slug>/update/',
        views.ProductFormUpdateView.as_view(),
        name='product_update'
    ),
    path(
        '<str:slug>/delete/',
        views.ProductFormDeleteView.as_view(),
        name='pruduct_delete'
    ),
    path(
        '<str:slug>/',
        views.ProductCardView.as_view(),
        name='product_card'
    ),
]
