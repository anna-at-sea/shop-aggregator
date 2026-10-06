from django.conf import settings

from honduras_shop_aggregator.cities.models import City


def city_context(request):
    capital_city = City.objects.get(pk=1)
    city_pk = request.session.get('city_pk')
    if city_pk:
        selected_city = City.objects.filter(pk=city_pk).first()
    else:
        selected_city = None
    if selected_city:
        city_selection_required = False
    else:
        selected_city = capital_city
        request.session['city_pk'] = selected_city.pk
        request.session['city_name'] = selected_city.name
        city_selection_required = True
    cities = City.objects.all().order_by('pk').exclude(pk=selected_city.pk)
    return {
        'current_city': selected_city,
        'cities': cities,
        'city_selection_required': city_selection_required
    }


def seller_features(request):
    return {
        'seller_features_enabled': settings.SELLER_FEATURES_ENABLED
    }


def user_mode(request):
    mode = request.session.get('mode', 'user')
    if not request.user.is_authenticated or not request.user.is_seller:
        mode = 'user'
        request.session['mode'] = 'user'
    return {
        'mode': mode
    }
