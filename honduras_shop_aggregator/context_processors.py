from honduras_shop_aggregator.cities.models import City


def city_context(request):
    capital_city = City.objects.get(pk=1)
    selected_city = None
    if request.session.get('city_pk'):
        selected_city = City.objects.get(pk=request.session.get('city_pk'))
    elif request.user.is_authenticated and request.user.preferred_delivery_city:
        selected_city = request.user.preferred_delivery_city
        request.session['city_pk'] = selected_city.pk
        request.session['city_name'] = selected_city.name
    else:
        selected_city = capital_city
        request.session['city_pk'] = selected_city.pk
        request.session['city_name'] = selected_city.name
    cities = City.objects.all().order_by('name')
    if selected_city:
        selected_pk = request.session.get('city_pk')
        cities = cities.exclude(pk=selected_pk)
    return {
        'current_city': selected_city,
        'cities': cities
    }
