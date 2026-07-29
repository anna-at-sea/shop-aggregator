from collections import OrderedDict

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django_filters.views import FilterView

from honduras_shop_aggregator import utils
from honduras_shop_aggregator.products.filters import ProductFilter
from honduras_shop_aggregator.products.forms import (ProductCreateForm,
                                                     ProductDeleteForm,
                                                     ProductImageUpdateForm,
                                                     ProductUpdateForm)
from honduras_shop_aggregator.products.models import (Product, ProductImage,
                                                      ProductVariation)


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["grouped_variations"] = OrderedDict()
        for variation in self.object.variations.all():
            context["grouped_variations"].setdefault(
                variation.display_type,
                []
            ).append(variation.value)
        return context


class ProductFilterView(
    utils.ProductFilterMixin, SuccessMessageMixin, FilterView,
):
    model = Product
    template_name = "pages/products/product_list.html"
    context_object_name = "products"
    filterset_class = ProductFilter
    paginate_by = 20

    def get_queryset(self):
        return self.get_base_queryset()

    def get_filterset(self, filterset_class):
        return self.get_product_filter()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = context["products"]
        if self.request.user.is_authenticated:
            liked_ids = set(
                self.request.user.likes.values_list(
                    "product_id",
                    flat=True,
                )
            )
            for product in products:
                product.is_liked = product.pk in liked_ids
        else:
            liked_products = set(
                self.request.session.get(
                    "liked_products",
                    [],
                )
            )
            for product in products:
                product.is_liked = product.pk in liked_products
        return context

    def render_to_response(self, context, **response_kwargs):
        request = self.request
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            products_html = render_to_string(
                "partials/_product_grid.html",
                {
                    "products": context["products"],
                    "request": request,
                },
                request=request,
            )
            filter_html = render_to_string(
                "partials/filter_form.html",
                {
                    "filter": context["filter"],
                },
                request=request,
            )
            page_obj = context["page_obj"]
            return JsonResponse({
                "html": products_html,
                "products_html": products_html,
                "filter_html": filter_html,
                "has_next": page_obj.has_next(),
                "next_page": (
                    page_obj.next_page_number()
                    if page_obj.has_next()
                    else None
                ),
            })
        return super().render_to_response(
            context,
            **response_kwargs,
        )


class ProductToggleActiveView(
    utils.UserLoginRequiredMixin, utils.SellerPermissionMixin, SuccessMessageMixin, View
):

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, slug=kwargs["slug"])
        if product.seller.user != request.user:
            messages.warning(
                    request,
                    _("You don't have permission to access this product.")
                )
            return redirect("index")
        product.is_active = not product.is_active
        product.save(update_fields=["is_active"])
        return JsonResponse({
            "success": True,
            "active": product.is_active,
            "price": str(product.product_price),
            "message": (
                _("Product activated")
                if product.is_active
                else _("Product hidden")
            )
        })


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
            "heading": _("Add Product"),
            "button_text": _("Add"),
            "variation_type_choices": ProductVariation.VariationType.choices,
            "context_variations": [],
            "show_variations": True,
        })
        return context

    def form_valid(self, form):
        form.instance.seller = self.request.user.seller
        self.object = form.save()
        self.save_variations()
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.instance.seller = self.request.user.seller
        return form

    def get_initial(self):
        initial = super().get_initial()
        seller = self.request.user.seller
        if seller.city:
            initial['origin_city'] = seller.city
        initial['delivery_cities'] = list(
            seller.delivery_cities.values_list('pk', flat=True)
        )
        return initial

    def save_variations(self):
        types = self.request.POST.getlist("variation_type")
        values = self.request.POST.getlist("variation_value")
        customs = self.request.POST.getlist("variation_custom_type")
        for index, (t, v, c) in enumerate(zip(types, values, customs), start=1):
            v = v.strip()
            if not v:
                continue
            ProductVariation.objects.create(
                product=self.object,
                variation_type=t,
                custom_type=c.strip() if t == "other" else "",
                value=v,
                order=index,
            )


class ProductImageManageView(
    utils.UserLoginRequiredMixin, utils.SellerPermissionMixin,
    SuccessMessageMixin, View
):
    template_name = 'pages/products/manage_images.html'
    slug_field = "slug"
    slug_url_kwarg = "slug"
    context_object_name = "product"

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_deleted=False)
        form = ProductImageUpdateForm(instance=product)
        context = {
            "heading": _("Manage Product Images"),
            "product": product,
            "form": form,
            "gallery": [
                {
                    "id": image.pk,
                    "url": image.image.url,
                    "order": image.order,
                }
                for image in product.gallery.all()
            ],
            "gallery_limit": 8,
            "gallery_count": product.gallery.count(),
            "remaining_images": 8 - product.gallery.count(),
        }
        return render(
            request,
            "pages/products/manage_images.html",
            context,
        )

    @transaction.atomic
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_deleted=False)
        form = ProductImageUpdateForm(
            request.POST,
            request.FILES,
            instance=product,
        )
        if not form.is_valid():
            context = {
                "heading": _("Manage Product Images"),
                "product": product,
                "form": form,
                "gallery": [
                    {
                        "id": image.pk,
                        "url": image.image.url,
                        "order": image.order,
                    }
                    for image in product.gallery.all()
                ],
                "gallery_limit": 8,
                "gallery_count": product.gallery.count(),
                "remaining_images": 8 - product.gallery.count(),
            }
            return render(
                request,
                self.template_name,
                context,
            )
        gallery_files = request.FILES.getlist("gallery_images")
        ids = request.POST.getlist("delete_images")
        remaining_existing = (
            product.gallery.count()
            - len(ids)
        )
        total_after_save = (
            remaining_existing
            + len(gallery_files)
        )
        if total_after_save > 8:
            form.add_error(
                None,
                _("Maximum of 8 gallery images allowed.")
            )
            context = {
                "heading": _("Manage Product Images"),
                "product": product,
                "form": form,
                "gallery": [
                    {
                        "id": image.pk,
                        "url": image.image.url,
                        "order": image.order,
                    }
                    for image in product.gallery.all()
                ],
                "gallery_limit": 8,
                "gallery_count": product.gallery.count(),
                "remaining_images": 8 - product.gallery.count(),
            }
            return render(
                request,
                self.template_name,
                context,
            )
        form.save()
        for image in ProductImage.objects.filter(product=product, pk__in=ids,):
            image.delete()
        existing_ids = set(
            product.gallery.values_list("pk", flat=True)
        )
        existing = {
            str(image.pk): image
            for image in product.gallery.all()
        }
        for file in gallery_files:
            ProductImage.objects.create(
                product=product,
                image=file,
            )
        gallery_order = request.POST.get("gallery_order", "")
        tokens = gallery_order.split(",")
        new_images = ProductImage.objects.filter(
            product=product
        ).exclude(
            pk__in=existing_ids
        ).order_by("pk")
        new_index = 0
        order = 1
        for token in tokens:
            if token.startswith("new-"):
                if new_index < len(new_images):
                    image = new_images[new_index]
                    image.order = order
                    image.save(update_fields=["order"])
                    new_index += 1
            elif token in existing:
                image = existing[token]
                image.order = order
                image.save(update_fields=["order"])
            order += 1
        messages.success(
            request,
            _("Images updated successfully.")
        )
        return redirect(
            "product_card",
            slug=product.slug,
        )


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
            'button_class': 'btn btn-secondary',
            'variation_type_choices': ProductVariation.VariationType.choices,
            'context_variations': [
                {
                    "variation_type": variation.variation_type,
                    "custom_type": variation.custom_type,
                    "value": variation.value,
                    "order": variation.order,
                }
                for variation in self.object.variations.all()
            ],
            'show_variations': True,
        })
        return context

    def form_valid(self, form):
        self.object = form.save()
        ProductVariation.objects.filter(
            product=self.object
        ).delete()
        self.save_variations()
        return super().form_valid(form)

    def save_variations(self):
        types = self.request.POST.getlist("variation_type")
        values = self.request.POST.getlist("variation_value")
        customs = self.request.POST.getlist("variation_custom_type")
        for index, (t, v, c) in enumerate(zip(types, values, customs), start=1):
            v = v.strip()
            if not v:
                continue
            ProductVariation.objects.create(
                product=self.object,
                variation_type=t,
                custom_type=c.strip() if t == "other" else "",
                value=v,
                order=index,
            )


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
        product.save(update_fields=["deleted_at", "is_deleted", "is_active"])
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
