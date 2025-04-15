from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from honduras_shop_aggregator import utils
from honduras_shop_aggregator.sellers.forms import (SellerCreateForm,
                                                    SellerDeleteForm,
                                                    SellerUpdateForm)
from honduras_shop_aggregator.sellers.models import Seller


class SellerProfileView(
    utils.UserLoginRequiredMixin, utils.UserPermissionMixin,
    SuccessMessageMixin, DetailView
):
    model = Seller
    template_name = 'pages/sellers/profile.html'
    context_object_name = 'seller'
    slug_field = "store_name"
    slug_url_kwarg = "store_name"

    def get_object(self):
        return get_object_or_404(Seller, store_name=self.kwargs["store_name"])


class SellerFormCreateView(
    SuccessMessageMixin, CreateView
):
    model = Seller
    form_class = SellerCreateForm
    template_name = 'layouts/base_form.html'

    def get_success_message(self, *args, **kwargs):
        return _("Shop is registered and awaiting verification")

    def get_success_url(self):
        return reverse_lazy(
            'user_profile', kwargs={'username': self.object.user.username}
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'heading': _("Seller Registration"),
            'button_text': _("Register")
        })
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class SellerFormUpdateView(
    utils.UserLoginRequiredMixin, utils.UserPermissionMixin,
    SuccessMessageMixin, UpdateView
):
    model = Seller
    form_class = SellerUpdateForm
    template_name = 'layouts/base_form.html'

    def get_object(self):
        return get_object_or_404(Seller, store_name=self.kwargs['store_name'])

    def get_success_url(self):
        return reverse_lazy(
            'seller_profile', kwargs={'store_name': self.object.store_name}
        )

    def get_success_message(self, *args, **kwargs):
        return _("Store is updated successfully")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'heading': _("Update store"),
            'button_text': _("Update")
        })
        return context


class SellerFormDeleteView(
    utils.UserLoginRequiredMixin, utils.UserPermissionMixin,
    SuccessMessageMixin, DeleteView
):
    form_class = SellerDeleteForm
    model = Seller
    template_name = 'layouts/base_form.html'
    success_url = reverse_lazy('index')

    def get_object(self):
        return get_object_or_404(Seller, store_name=self.kwargs['store_name'])

    def get_success_message(self, *args, **kwargs):
        return _("Store deleted successfully")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        object = self.get_object()
        context.update({
            'delete_prompt': (
                _("Are you sure you want to delete store ") + f"{object}?"
            ),
            'button_class': 'btn btn-danger',
            'button_text': _("Yes, delete")
        })
        return context
