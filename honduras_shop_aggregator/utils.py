import hashlib

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _


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
                _("Only verified sellers can add and edit products.")
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


def validate_image(image):
    max_size_mb = 15
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(_(f"Image size should not exceed {max_size_mb} MB."))


def image_upload_path(instance, filename):
    extension = filename.split('.')[-1]
    folder = f"{instance._meta.verbose_name.lower()}s"
    return f"{folder}/{instance.slug}.{extension.lower()}"


def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
