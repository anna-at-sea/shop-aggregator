import random

from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.cities.models import City
from honduras_shop_aggregator.products.models import Product


class IndexView(SuccessMessageMixin, ListView):
    model = Product
    template_name = "pages/index.html"
    context_object_name = "products"
    paginate_by = 24

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True, stock_quantity__gt=0)
        city_pk = self.request.session.get('city_pk')
        if city_pk:
            queryset = queryset.filter(
                Q(origin_city=city_pk) | Q(delivery_cities=city_pk)
            ).distinct()
        page = self.request.GET.get("page", "1")
        print(f'page: {page}')
        if page == "1":
            seed = random.randint(0, 9999999)
            self.request.session["shuffle_seed"] = seed
            self.request.session.modified = True
        else:
            seed = self.request.session.get("shuffle_seed", 1)
        print(f'seed: {seed}')
        products = list(queryset)
        # this needs to be changed when number of products grows
        random.Random(seed).shuffle(products)
        return products

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
        context["categories"] = Category.objects.all()[:6]
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


class SetCityView(View):

    def get(self, request, city_pk):
        city = get_object_or_404(City, pk=city_pk)
        request.session['city_pk'] = city.pk
        request.session['city_name'] = city.name

        return redirect(request.META.get('HTTP_REFERER', '/'))


@require_POST
def switch_mode(request):
    mode = request.POST.get("mode")
    if mode in ["user", "seller"]:
        request.session["mode"] = mode
    return redirect(request.META.get("HTTP_REFERER", "index"))
