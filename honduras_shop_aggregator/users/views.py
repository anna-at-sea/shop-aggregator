from django.contrib.auth.views import LoginView  #, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
# from django.views.generic.edit import CreateView, DeleteView, UpdateView

# from task_manager import utils
# from task_manager.user.forms import UserForm
from honduras_shop_aggregator.users.models import User


class UserProfileView(DetailView):
    model = User
    template_name = 'pages/users/profile.html'
    context_object_name = 'user'
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_object(self):
        return get_object_or_404(User, username=self.kwargs["username"])

class UserLoginView(SuccessMessageMixin, LoginView):
    template_name = 'layouts/base_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'heading': _("Log in"),
            'button_text': _("Log in")
        })
        return context

    def get_success_url(self):
        return reverse_lazy('index')

    def get_success_message(self, *args, **kwargs):
        return _("You are logged in")

# class UserFormCreateView(
#     utils.CreateViewMixin, SuccessMessageMixin, CreateView
# ):
#     model = User
#     form_class = UserForm

#     def get_success_message(self, *args, **kwargs):
#         return _("User is registered successfully")

#     def get_success_url(self):
#         return reverse_lazy('login')

#     def get_context_data(self, *args, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context.update({
#             'heading': _("Registration"),
#             'button_text': _("Register")
#         })
#         return context


# class UserFormUpdateView(
#     utils.UpdateViewMixin, utils.UserLoginRequiredMixin,
#     utils.UserPermissionMixin, SuccessMessageMixin, UpdateView
# ):
#     model = User
#     form_class = UserForm


# class UserFormDeleteView(
#     utils.DeleteViewMixin, utils.UserLoginRequiredMixin,
#     utils.UserPermissionMixin, SuccessMessageMixin, DeleteView
# ):
#     model = User
