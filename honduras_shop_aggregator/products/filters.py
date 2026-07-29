import re

import django_filters
from django.db.models import Case, IntegerField, Q, When
from django.utils.translation import gettext_lazy as _
from unidecode import unidecode

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.sellers.models import Seller


class ProductFilter(django_filters.FilterSet):

    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label=_("Category")
    )
    seller = django_filters.ModelChoiceFilter(
        queryset=Seller.objects.filter(is_deleted=False),
        label=_("Sold by")
    )
    price_min = django_filters.NumberFilter(
        field_name="product_price",
        lookup_expr='gte',
        label=_("Price from")
    )
    price_max = django_filters.NumberFilter(
        field_name="product_price",
        lookup_expr='lte',
        label=_("Price to")
    )
    search = django_filters.CharFilter(method='filter_search', label=_("Search"))

    class Meta:
        model = Product
        fields = ['category', 'seller', 'price_min', 'price_max']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        normalized_value = unidecode(value.strip().lower())
        cleaned_value = re.sub(r"[^\w\s]|_", " ", normalized_value)
        terms = cleaned_value.split()
        for term in terms:
            queryset = queryset.filter(
                Q(product_name__icontains=term) |
                Q(description__icontains=term)
            )
        queryset = queryset.annotate(
            name_exact=Case(
                When(product_name__iexact=value.strip(), then=1),
                default=0,
                output_field=IntegerField()
            )
        ).order_by('-name_exact', 'product_name')
        return queryset

    def get_filtered_products(self, queryset):
        products = queryset
        category = self.data.get("category")
        if category:
            products = products.filter(category=category)
        search = self.data.get("search")
        if search:
            products = self.filter_search(products, "search", search)
        return products

    @property
    def show_seller_filter(self):
        return bool(
            self.data.get("category") or self.data.get("search")
        )

    def __init__(
        self,
        *args,
        category_locked=False,
        available_products=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if category_locked and "category" in self.filters:
            self.filters.pop("category")
        if available_products is None:
            return
        products = self.get_filtered_products(available_products)
        self.filters["seller"].queryset = (
            Seller.objects.filter(
                seller_products__in=products,
                is_deleted=False,
            )
            .distinct()
        )
