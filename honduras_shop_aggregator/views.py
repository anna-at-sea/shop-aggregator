from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic.base import TemplateView

from honduras_shop_aggregator.cities.models import City


class IndexView(TemplateView):
    template_name = 'pages/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class SetCityView(View):

    def get(self, request, city_pk):
        city = get_object_or_404(City, pk=city_pk)
        request.session['city_pk'] = city.pk
        request.session['city_name'] = city.name

        return redirect(request.META.get('HTTP_REFERER', '/'))
