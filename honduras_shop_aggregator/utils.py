from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.messages import get_messages
# from django.core.exceptions import ValidationError
# from django.db.models import ProtectedError
from django.shortcuts import redirect
# from django.test import TestCase
# from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _


class UserLoginRequiredMixin(LoginRequiredMixin):

    def handle_no_permission(self):
        messages.error(self.request, _("You are not logged in! Please log in."))
        return redirect('login')
        

class UserPermissionMixin:

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (
            kwargs.get('username') != request.user.username
        ):
            messages.error(
                request, _("You don't have permission to edit this user.")
            )
            return redirect('index')
        return super().dispatch(request, *args, **kwargs)
