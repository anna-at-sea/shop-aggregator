from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django_filters.views import FilterView

from honduras_shop_aggregator import utils
from honduras_shop_aggregator.products.filters import ProductFilter
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
        product = get_object_or_404(Product, slug=self.kwargs["slug"])
        if product.is_deleted:
            raise Http404(_("Product not found"))
        if self.request.user.pk:
            product.is_liked = product.likes.filter(user=self.request.user).exists()
        return product


class ProductFilterView(SuccessMessageMixin, FilterView):
    model = Product
    template_name = 'pages/products/product_list.html'
    context_object_name = 'products'
    filterset_class = ProductFilter
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True, stock_quantity__gt=0)
        city_pk = self.request.session.get('city_pk')
        if city_pk:
            queryset = queryset.filter(
                Q(origin_city=city_pk) | Q(delivery_cities=city_pk)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = context['products']
        if self.request.user.is_authenticated:
            liked_ids = self.request.user.likes.values_list("product_id", flat=True)
            for product in products:
                product.is_liked = product.pk in liked_ids
        else:
            liked_products = self.request.session.get('liked_products', [])
            for product in products:
                product.is_liked = product.pk in liked_products
        return context

    def render_to_response(self, context, **response_kwargs):
        """Return JSON if AJAX, otherwise full page."""
        request = self.request
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            html = render_to_string(
                "partials/_product_grid.html", 
                {"products": context["products"], "request": request},
                request=request
            )
            page_obj = context["page_obj"]
            return JsonResponse({
                "html": html,
                "has_next": page_obj.has_next(),
                "next_page": (
                    page_obj.next_page_number() if page_obj.has_next() else None
                )
            })
        return super().render_to_response(context, **response_kwargs)


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
        form.instance.seller = self.request.user.seller
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


class ProductSoftDeleteView(
    utils.UserLoginRequiredMixin, utils.SellerPermissionMixin,
    SuccessMessageMixin, UpdateView
):
    form_class = ProductDeleteForm
    model = Product
    template_name = 'layouts/base_form.html'

    def get_object(self):
        self.object = get_object_or_404(Product, slug=self.kwargs['slug'])
        return self.object

    def form_valid(self, form):
        product = form.save(commit=False)
        product.is_deleted = True  # to remove from seller queryset
        product.deleted_at = timezone.now()
        product.is_active = False  # to remove from users querysets
        product.save(update_fields=["is_deleted", "is_active"])
        return super().form_valid(form)

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
