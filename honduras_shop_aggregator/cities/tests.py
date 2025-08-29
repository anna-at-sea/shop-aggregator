from django.db.models import ProtectedError
from django.urls import reverse
from django.utils.translation import gettext as _

from honduras_shop_aggregator.cities.models import City
from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase


class TestDefaultSessionCity(BaseTestCase):

    def setUp(self):
        self.user_without_city = User.objects.get(pk=1)
        self.user_with_city = User.objects.get(username='userwithpreferredcity')

    def test_default_city_fallback_anonymous(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(self.client.session.get('city_pk'), 1)
        self.assertContains(response, 'Capital')

    def test_default_city_fallback_user_without_preferred_city(self):
        self.login_user(self.user_without_city)
        response = self.client.get(reverse('index'))
        self.assertEqual(self.client.session.get('city_pk'), 1)
        self.assertContains(response, 'Capital')

    def test_default_city_for_user_with_preferred_city(self):
        self.login_user(self.user_with_city)
        response = self.client.get(reverse('index'))
        self.assertEqual(self.client.session.get('city_pk'), 2)
        self.assertContains(response, 'Second City')


class TestSetCity(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_set_city_with_toggle_anonymous(self):
        response = self.client.get(reverse(
            'set_city',
            kwargs={'city_pk': 2}),
            follow=True
        )
        self.assertEqual(self.client.session.get('city_pk'), 2)
        self.assertContains(response, 'Second City')
        response2 = self.client.get(reverse(
            'set_city',
            kwargs={'city_pk': 1}),
            follow=True
        )
        self.assertEqual(self.client.session.get('city_pk'), 1)
        self.assertContains(response2, 'Capital')

    def test_set_city_with_toggle_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'set_city',
            kwargs={'city_pk': 2}),
            follow=True
        )
        self.assertEqual(self.client.session.get('city_pk'), 2)
        self.assertContains(response, 'Second City')

class TestFilterProductsByCity(BaseTestCase):

    def setUp(self):
        self.product_from_capital_with_delivery = Product.objects.get(pk=1)
        self.product_from_capital_without_delivery = Product.objects.get(pk=4)
        self.product_from_second_city = Product.objects.get(pk=6)
        self.other_category_product_from_capital = Product.objects.get(pk=5)

    def test_filter_products_for_capital(self):
        self.client.get(reverse('set_city', kwargs={'city_pk': 1}))
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testproduct')
        self.assertNotContains(response, 'unavailable_product')
        self.assertNotContains(response, 'out_of_stock_product')
        self.assertContains(response, 'other_seller_product')
        self.assertContains(response, 'other category product')
        self.assertNotContains(response, 'product_from_second_city')

    def test_filter_products_for_second_city(self):
        self.client.get(reverse('set_city', kwargs={'city_pk': 2}))
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'testproduct')
        self.assertNotContains(response, 'unavailable_product')
        self.assertNotContains(response, 'out_of_stock_product')
        self.assertNotContains(response, 'other_seller_product')
        self.assertNotContains(response, 'other category product')
        self.assertContains(response, 'product_from_second_city')

    def test_view_products_for_second_city(self):
        self.client.get(reverse('set_city', kwargs={'city_pk': 2}))
        response = self.client.get(
            reverse(
                'product_card',
                kwargs={'slug': self.product_from_second_city.slug}
            )
        )
        self.assertContains(response, _('Available in your city'))
        response2 = self.client.get(
            reverse(
                'product_card',
                kwargs={'slug': self.product_from_capital_with_delivery.slug}
            )
        )
        print(self.product_from_capital_with_delivery.origin_city.pk)
        print(self.client.session.get('city_pk'))
        self.assertContains(response2, _('Delivery from'))
        response3 = self.client.get(
            reverse(
                'product_card',
                kwargs={'slug': self.product_from_capital_without_delivery.slug}
            )
        )
        self.assertContains(response3, _('Not available in your city'))

    def test_view_category_page_for_different_cities(self):
        self.client.get(reverse('set_city', kwargs={'city_pk': 1}))
        response = self.client.get(
            reverse(
                'category_page',
                kwargs={'slug': self.other_category_product_from_capital.category.slug}
            )
        )
        self.assertContains(response, 'other category product')
        response2 = self.client.get(
            reverse('set_city', kwargs={'city_pk': 2}),
            HTTP_REFERER=reverse(
                'category_page',
                kwargs={'slug': self.other_category_product_from_capital.category.slug}
            ),
            follow=True
        )
        self.assertNotContains(response2, 'other category product')
        self.assertContains(response2, _('No products found.'))


class TestCityProtect(BaseTestCase):

    def setUp(self):
        self.city_1 = City.objects.get(pk=1)
        self.city_2 = City.objects.get(pk=2)
        self.product_1 = Product.objects.get(pk=1)
        self.user_2 = User.objects.get(username='userwithpreferredcity')

    def test_city_protect_on_delete_product_connected(self):
        self.assertEqual(self.product_1.origin_city, self.city_1)
        with self.assertRaises(ProtectedError):
            self.city_1.delete()

    def test_city_protect_on_delete_user_connected(self):
        self.assertEqual(self.user_2.preferred_delivery_city, self.city_2)
        with self.assertRaises(ProtectedError):
            self.city_2.delete()
