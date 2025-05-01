# from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404  # , redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, UpdateView  # , DeleteView

from honduras_shop_aggregator import utils
from honduras_shop_aggregator.products.forms import (ProductCreateForm,
                                                     ProductImageUpdateForm)
from honduras_shop_aggregator.products.models import Product


class ProductCardView(
    SuccessMessageMixin, DetailView
):
    model = Product
    template_name = 'pages/products/product_card.html'
    context_object_name = 'product'
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])


class ProductListView(SuccessMessageMixin, ListView):
    model = Product
    template_name = 'pages/products/product_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = Product.objects.filter(
            is_active=True, stock_quantity__gt=0
        )
        return context


class ProductFormCreateView(
    utils.UserLoginRequiredMixin, utils.SellerPermissionMixin,
    SuccessMessageMixin, CreateView
):
    model = Product
    form_class = ProductCreateForm
    template_name = 'layouts/base_form.html'

    def get_success_message(self, *args, **kwargs):
        return _("Product is added successfully. Please add image of the product")

    def get_success_url(self):
        return reverse_lazy(
            'product_update_image', kwargs={'slug': self.object.slug}
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'heading': _("Add Product"),
            'button_text': _("Add")
        })
        return context

    def form_valid(self, form):
        form.instance.seller = self.request.user.seller
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.seller = self.request.user.seller  # Assign early
        return form


class ProductFormUpdateImageView(
    utils.UserLoginRequiredMixin, utils.SellerPermissionMixin,
    SuccessMessageMixin, UpdateView
):
    model = Product
    form_class = ProductImageUpdateForm
    template_name = 'layouts/base_form.html'
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "product"

    def get_success_message(self, *args, **kwargs):
        return _("Image updated successfully")

    def get_success_url(self):
        return reverse_lazy('product_card', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'heading': _("Update Product Image"),
            'button_text': _("Update Image"),
            'form': self.get_form()
        })
        return context
