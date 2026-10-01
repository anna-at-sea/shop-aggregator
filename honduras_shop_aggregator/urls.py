from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from honduras_shop_aggregator.likedproducts.views import ToggleLikeView

from . import views

urlpatterns = i18n_patterns(
    path('i18n/', include('django.conf.urls.i18n')),
    path('', views.IndexView.as_view(), name='index'),
    path('users/', include('honduras_shop_aggregator.users.urls')),
    path('sellers/', include('honduras_shop_aggregator.sellers.urls')),
    path('products/', include('honduras_shop_aggregator.products.urls')),
    path('categories/', include('honduras_shop_aggregator.categories.urls')),
    path('set-city/<int:city_pk>/', views.SetCityView.as_view(), name='set_city'),
    path('toggle-like/<int:product_pk>/', ToggleLikeView.as_view(), name='toggle_like'),
    path('switch-mode/', views.switch_mode, name='switch_mode'),
    path('admin/', admin.site.urls),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
