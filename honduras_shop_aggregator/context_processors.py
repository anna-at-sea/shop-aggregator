from django.conf import settings

from honduras_shop_aggregator.cities.models import City


def city_context(request):
    capital_city = City.objects.get(pk=1)
    if request.session.get('city_pk'):
        selected_city = City.objects.get(pk=request.session.get('city_pk'))
    else:
        selected_city = capital_city
        request.session['city_pk'] = selected_city.pk
        request.session['city_name'] = selected_city.name
    cities = City.objects.all().order_by('name').exclude(pk=selected_city.pk)
    return {
        'current_city': selected_city,
        'cities': cities
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
