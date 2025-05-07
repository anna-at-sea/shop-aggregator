# import json
# from os.path import join

from django.urls import reverse
from django.utils.translation import gettext as _

from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase

FIXTURE_PATH = 'honduras_shop_aggregator/fixtures/'

class TestProductCardRead(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()
        self.product_active = Product.objects.all().first()
        self.product_not_active = Product.objects.get(pk=2)
        self.product_out_of_stock = Product.objects.get(pk=3)

    def test_read_product_card_unauthorized(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_active.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("In stock"))
        self.assertContains(response, _("Login to Save"))

    def test_read_product_card_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_active.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("In stock"))
        self.assertContains(response, _("Add to Favorites"))

    def test_read_product_card_not_active(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_not_active.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Out of stock"))
        self.assertNotContains(response, _("Add to Favorites"))
        self.assertNotContains(response, _("Login to Save"))

    def test_read_product_card_out_of_stock(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_out_of_stock.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Out of stock"))
        self.assertNotContains(response, _("Add to Favorites"))
        self.assertNotContains(response, _("Login to Save"))

    def test_read_product_non_existent(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': 'non-existent-product'}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_read_product_with_malformed_slug(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': '%%%weird---slug%%%'}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)
