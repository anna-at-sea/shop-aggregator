from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.CategoryListView.as_view(),
        name='category_list'
    ),
    path(
        '<str:slug>/',
        views.CategoryPageView.as_view(),
        name='category_page'
    ),
]
