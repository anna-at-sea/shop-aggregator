from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import DetailView, ListView

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.products.models import Product


class CategoryListView(SuccessMessageMixin, ListView):
    model = Category
    template_name = 'pages/categories/category_list.html'
    context_object_name = 'categories'


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
        context["products"] = Product.objects.filter(
            category=self.object,
            is_active=True
        )
        return context
