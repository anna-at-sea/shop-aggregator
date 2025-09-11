from django.conf import settings
from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.SellerListView.as_view(),
        name='seller_list'
    ),
]

if settings.SELLER_FEATURES_ENABLED:
    urlpatterns += [
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

urlpatterns += [
    path(
        '<str:store_name>/',
        views.PublicSellerProfileView.as_view(),
        name='public_seller_profile'
    ),
]
