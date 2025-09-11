from django.conf import settings
from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.ProductFilterView.as_view(),
        name='product_list'
    ),
]

if settings.SELLER_FEATURES_ENABLED:
    urlpatterns += [
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
            views.ProductSoftDeleteView.as_view(),
            name='product_delete'
        ),
    ]

urlpatterns += [
    path(
        '<str:slug>/',
        views.ProductCardView.as_view(),
        name='product_card'
    ),
]
