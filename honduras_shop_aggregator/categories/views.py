from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.views.generic import DetailView, ListView

from honduras_shop_aggregator.categories.models import Category
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
    SuccessMessageMixin, DetailView
):
    model = Category
    template_name = 'pages/categories/category_page.html'
    context_object_name = 'category'
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city_pk = self.request.session.get('city_pk')
        products = Product.objects.filter(
            category=self.object,
            is_active=True,
            stock_quantity__gt=0
        )
        if city_pk:
            products = products.filter(
                Q(origin_city=city_pk) | Q(delivery_cities=city_pk)
            )
        context["products"] = products.distinct()
        return context
