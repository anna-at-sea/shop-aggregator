from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages import get_messages
# from django.core.exceptions import ValidationError
# from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext as _


class UserLoginRequiredMixin(LoginRequiredMixin):

    def handle_no_permission(self):
        messages.warning(self.request, _("You are not logged in! Please log in."))
        return redirect('login')


class UserPermissionMixin:

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (
            kwargs.get('username') != request.user.username
        ):
            messages.warning(
                request, _(
                    "You don't have permission to view or edit other user."
                )
            )
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)


class BaseTestCase(TestCase):
    fixtures = ["users.json"]

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
