from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView
from django_filters.views import FilterView

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.products.filters import ProductFilter
from honduras_shop_aggregator.products.models import Product


class CategoryListView(SuccessMessageMixin, ListView):
    model = Category
    template_name = 'pages/categories/category_list.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city_pk = self.request.session.get('city_pk')
        for category in context['categories']:
            products = Product.objects.filter(
                category=category,
                is_active=True,
                stock_quantity__gt=0
            )
            if city_pk:
                products = products.filter(
                    Q(origin_city=city_pk) | Q(delivery_cities=city_pk)
                )
            category.product_count = products.distinct().count()
        return context


class CategoryPageView(
    SuccessMessageMixin, FilterView
):
    model = Product
    template_name = 'pages/categories/category_page.html'
    context_object_name = 'products'
    filterset_class = ProductFilter
    paginate_by = 20

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['category_locked'] = True 
        return kwargs

    def get_queryset(self, **kwargs):
        category_slug = self.kwargs.get("slug")
        city_pk = self.request.session.get('city_pk')
        products = Product.objects.filter(
            category__slug=category_slug,
            is_active=True,
            stock_quantity__gt=0
        )
        if city_pk:
            products = products.filter(
                Q(origin_city=city_pk) | Q(delivery_cities=city_pk)
            ).distinct()
        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = get_object_or_404(Category, slug=self.kwargs.get("slug"))
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
