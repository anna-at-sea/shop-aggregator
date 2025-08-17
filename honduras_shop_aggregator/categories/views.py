from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
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
        for product in products:
            if self.request.user.is_authenticated:
                product.is_liked = product.likes.filter(user=self.request.user).exists()
            else:
                product.is_liked = product in self.request.session.get(
                    'liked_products', []
                )
        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = get_object_or_404(Category, slug=self.kwargs.get("slug"))
        return context
