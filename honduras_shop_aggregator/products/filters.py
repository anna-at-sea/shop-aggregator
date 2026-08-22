import numbers

import django_filters
from django import forms
from django.contrib.postgres.lookups import Unaccent
from django.contrib.postgres.search import (SearchQuery, SearchRank,
                                            SearchVector, TrigramSimilarity)
from django.db.models import CharField, Count, F, FloatField, Q, Value
from django.utils.translation import gettext_lazy as _

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.sellers.models import Seller

CharField.register_lookup(Unaccent)

class ProductFilter(django_filters.FilterSet):

    SORT_CHOICES = (
        ("newest", _("Newest")),
        ("price_asc", _("Price: Low to High")),
        ("price_desc", _("Price: High to Low")),
        ("saved", _("Most Saved")),
    )

    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label=_("Category")
    )
    seller = django_filters.ModelMultipleChoiceFilter(
        field_name="seller",
        queryset=Seller.objects.none(),
        label=_("Sold by"),
        widget=forms.CheckboxSelectMultiple,
    )
    price_min = django_filters.NumberFilter(
        field_name="product_price",
        lookup_expr="gte",
        label="",
    )
    price_max = django_filters.NumberFilter(
        field_name="product_price",
        lookup_expr="lte",
        label="",
    )
    search = django_filters.CharFilter(method='filter_search', label=_("Search"))
    sort = django_filters.ChoiceFilter(
        choices=SORT_CHOICES,
        method="filter_sort",
        label=_("Sort by"),
        empty_label=None,
    )

    class Meta:
        model = Product
        fields = ['category', 'seller', 'price_min', 'price_max', 'sort']

    def filter_search(self, queryset, name, value):
        value = value.strip()

        if not value:
            return queryset

        terms = value.split()

        name_vector = SearchVector(
            "product_name",
            weight="A",
            config="spanish",
        )

        description_vector = SearchVector(
            "description",
            weight="B",
            config="spanish",
        )

        annotations = {}
        combined_filter = Q()

        for index, term in enumerate(terms):
            search_query = SearchQuery(
                term,
                search_type="websearch",
                config="spanish",
            )

            name_rank = SearchRank(
                name_vector,
                search_query,
            )

            description_rank = SearchRank(
                description_vector,
                search_query,
            )

            similarity = TrigramSimilarity(
                "product_name",
                term,
            )

            annotations[f"name_rank_{index}"] = name_rank
            annotations[f"description_rank_{index}"] = description_rank
            annotations[f"similarity_{index}"] = similarity

            # EACH term must match.
            combined_filter &= (
                Q(**{f"name_rank_{index}__gt": 0})
                | Q(**{f"description_rank_{index}__gt": 0})
                | Q(**{f"similarity_{index}__gt": 0.15})
            )

        queryset = queryset.annotate(**annotations)

        queryset = queryset.filter(combined_filter)

        # Sum relevance from all search terms.
        relevance = Value(
            0,
            output_field=FloatField(),
        )

        for index in range(len(terms)):
            relevance = (
                relevance
                + F(f"name_rank_{index}")
                + F(f"description_rank_{index}")
                + F(f"similarity_{index}")
            )

        queryset = queryset.annotate(
            relevance=relevance,
        )

        return queryset.order_by(
            "-relevance",
            "-date_added",
        )

    def filter_sort(self, queryset, name, value):
        if value == "price_asc":
            return queryset.order_by("product_price", "-id")
        if value == "price_desc":
            return queryset.order_by("-product_price", "-id")
        if value == "saved":
            return (
                queryset
                .annotate(saved_count=Count("likes", distinct=True))
                .order_by("-saved_count", "-id")
            )
        if value == "newest":
            return queryset.order_by("-date_added", "-id")
        return queryset.order_by("-id")

    def get_filtered_products(self, queryset):
        products = queryset
        category = self.data.get("category")
        if category:
            products = products.filter(category=category)
        search = self.data.get("search")
        if search:
            products = self.filter_search(products, "search", search)
        price_min = self.data.get("price_min")
        if price_min and isinstance(price_min, numbers.Number):
            products = products.filter(product_price__gte=price_min)
        price_max = self.data.get("price_max")
        if price_max and isinstance(price_max, numbers.Number):
            products = products.filter(product_price__lte=price_max)
        return products

    @property
    def show_seller_filter(self):
        return (
            self.category_locked
            or bool(
                self.data.get("category")
                or self.data.get("search")
            )
        )

    def __init__(
        self,
        *args,
        category_locked=False,
        available_products=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.category_locked = category_locked
        if not self.data.get("sort"):
            self.form.initial["sort"] = "newest"
        self.form.fields["price_min"].widget.attrs.update({
            "placeholder": _("Min"),
        })
        self.form.fields["price_max"].widget.attrs.update({
            "placeholder": _("Max"),
        })
        if category_locked:
            self.form.fields.pop("category", None)
        if available_products is None:
            return
        products = self.get_filtered_products(available_products)
        seller_queryset = (
            Seller.objects.filter(
                seller_products__in=products,
                is_deleted=False,
            )
            .annotate(
                product_count=Count(
                    "seller_products",
                    filter=Q(seller_products__in=products),
                    distinct=True,
                )
            )
            .order_by("-product_count", "store_name")
            .distinct()
        )
        self.form.fields["seller"].queryset = seller_queryset
        self.form.fields["seller"].label_from_instance = (
            lambda obj: f"{obj.store_name} ({obj.product_count})"
        )