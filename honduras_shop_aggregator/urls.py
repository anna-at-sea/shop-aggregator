from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('users/', include('honduras_shop_aggregator.users.urls')),
    path('admin/', admin.site.urls),
]
