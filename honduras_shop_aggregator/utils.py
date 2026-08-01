from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages import get_messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _

from honduras_shop_aggregator.products.filters import ProductFilter
from honduras_shop_aggregator.products.models import Product

from .image_utils import get_file_hash, image_upload_path, validate_image

__all__ = [
    "get_file_hash",
    "image_upload_path",
    "validate_image",
]


class UserLoginRequiredMixin(LoginRequiredMixin):

    def handle_no_permission(self):
        messages.warning(self.request, _("You are not logged in! Please log in."))
        return redirect('login')


class UserPermissionMixin:

    def dispatch(self, request, *args, **kwargs):
        auth = request.user.is_authenticated
        username_in_kwargs = kwargs.get('username')
        store_in_kwargs = kwargs.get('store_name')
        user_match = (kwargs.get('username') == request.user.username)
        store_match = (
            request.user.is_seller and
            kwargs.get('store_name') == request.user.seller.store_name
        )
        if auth and username_in_kwargs and not user_match:
            messages.warning(
                request, _(
                    "You don't have permission to view or edit other user."
                )
            )
            return redirect('index')
        if auth and store_in_kwargs and not store_match:
            messages.warning(
                request, _(
                    "You don't have permission to access other store profile."
                )
            )
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class SellerPermissionMixin:

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_seller and request.user.seller.is_verified):
            messages.warning(
                request,
                _("Only verified sellers with active store can add and edit products.")
            )
            return redirect('index')
        if kwargs.get('slug'):
            from honduras_shop_aggregator.products.models import Product
            product = get_object_or_404(Product, slug=kwargs.get('slug'))
            if product.seller != request.user.seller:
                messages.warning(
                    request,
                    _("You don't have permission to access this product.")
                )
                return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class BaseTestCase(TestCase):
    fixtures = [
        "users.json",
        "sellers.json",
        "products.json",
        "categories.json",
        "cities.json"
    ]

    def login_user(self, user):
        self.client.login(
            username=user.username,
            password="correct_password"
        )

    def assertRedirectWithMessage(
        self,
        response,
        redirect_to='login',
        message=_("You are not logged in! Please log in."),
        reverse_kwargs=None
    ):
        self.assertRedirects(response, reverse(redirect_to, kwargs=reverse_kwargs))
        self.assertTrue(get_messages(response.wsgi_request))
        self.assertContains(response, message)


class ProductFilterMixin:

    def get_category_slug(self):
        return None

    def get_base_queryset(self):
        queryset = Product.objects.filter(
            is_active=True,
            stock_quantity__gt=0,
            is_deleted=False,
        )
        category_slug = self.get_category_slug()
        if category_slug:
            queryset = queryset.filter(
                category__slug=category_slug,
            )
        city_pk = self.request.session.get("city_pk")
        if city_pk:
            queryset = queryset.filter(
                Q(origin_city=city_pk) |
                Q(delivery_cities=city_pk)
            ).distinct()
        return queryset

    def get_product_filter(self):
        queryset = self.get_base_queryset()
        return ProductFilter(
            self.request.GET,
            queryset=queryset,
            available_products=queryset,
            category_locked=bool(self.get_category_slug()),
        )
