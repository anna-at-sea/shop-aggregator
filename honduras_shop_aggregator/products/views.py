# from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404  # , redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from honduras_shop_aggregator import utils
from honduras_shop_aggregator.products.forms import (ProductCreateForm,
                                                     ProductDeleteForm,
                                                     ProductImageUpdateForm,
                                                     ProductUpdateForm)
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


class ProductFormUpdateView(
    utils.UserLoginRequiredMixin, utils.SellerPermissionMixin,
    SuccessMessageMixin, UpdateView
):
    model = Product
    form_class = ProductUpdateForm
    template_name = 'layouts/base_form.html'

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs['slug'])

    def get_success_url(self):
        return reverse_lazy(
            'product_card', kwargs={'slug': self.object.slug}
        )

    def get_success_message(self, *args, **kwargs):
        return _("Product information is updated successfully")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'heading': _("Update product"),
            'button_text': _("Update"),
            'button_class': 'btn btn-secondary'
        })
        return context


class ProductFormDeleteView(
    utils.UserLoginRequiredMixin, utils.SellerPermissionMixin,
    SuccessMessageMixin, DeleteView
):
    form_class = ProductDeleteForm
    model = Product
    template_name = 'layouts/base_form.html'

    def get_object(self):
        self.object = get_object_or_404(Product, slug=self.kwargs['slug'])
        return self.object

    def get_success_url(self):
        return reverse_lazy(
            'seller_profile', kwargs={'store_name': self.request.user.seller.store_name}
        )

    def get_success_message(self, *args, **kwargs):
        return _("Product deleted successfully")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'delete_prompt': (
                _("Are you sure you want to delete product ") + f"{self.object}?"
            ),
            'button_class': 'btn btn-danger',
            'button_text': _("Yes, delete")
        })
        return context
