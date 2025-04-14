from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = i18n_patterns(
    path('i18n/', include('django.conf.urls.i18n')),
    path('', views.IndexView.as_view(), name='index'),
    path('users/', include('honduras_shop_aggregator.users.urls')),
    path('sellers/', include('honduras_shop_aggregator.sellers.urls')),
    path('admin/', admin.site.urls),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
