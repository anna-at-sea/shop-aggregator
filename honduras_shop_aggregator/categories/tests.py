from django.db.models import ProtectedError
from django.urls import reverse
from django.utils.translation import gettext as _

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase


class TestCategoryPageRead(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()
        self.category = Category.objects.all().first()

    def test_read_category_page_unauthorized(self):
        response = self.client.get(reverse(
            'category_page', kwargs={'slug': self.category.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "general")
        self.assertContains(response, "testproduct")

    def test_read_category_page_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'category_page', kwargs={'slug': self.category.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "general")
        self.assertContains(response, "testproduct")

    def test_read_category_page_no_products(self):
        empty_category = Category.objects.get(pk=2)
        response = self.client.get(reverse(
            'category_page', kwargs={'slug': empty_category.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("No products found."))

    def test_only_category_products_shown(self):
        response = self.client.get(reverse(
            'category_page', kwargs={'slug': self.category.slug}),
            follow=True
        )
        self.assertNotContains(response, "other category product")

    def test_read_category_non_existent(self):
        response = self.client.get(reverse(
            'category_page', kwargs={'slug': 'non-existent-category'}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_read_category_with_malformed_slug(self):
        response = self.client.get(reverse(
            'category_page', kwargs={'slug': '%%%weird---slug%%%'}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)


class TestCategoryListRead(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()
        self.category = Category.objects.all().first()
        self.other_category = Category.objects.get(pk=2)
        self.product_count_first_category = Product.objects.filter(category=1).count()
        self.product_count_second_category = Product.objects.filter(category=2).count()

    def test_read_category_list_unauthorized(self):
        response = self.client.get(
            reverse('category_list'),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)
        self.assertContains(response, self.other_category.name)
        self.assertContains(
            response, _(f'{self.product_count_first_category} products')
        )
        self.assertContains(
            response, _(f'{self.product_count_second_category} product')
        )

    def test_read_category_list_authorized(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse('category_list'),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)
        self.assertContains(response, self.other_category.name)

    def test_read_category_list_empty(self):
        Product.objects.all().delete()
        Category.objects.all().delete()
        response = self.client.get(reverse('category_list'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("No categories found."))


class TestCategoryProtect(BaseTestCase):

    def setUp(self):
        self.category = Category.objects.all().first()
        self.product = Product.objects.all().first()

    def test_category_protect_on_delete(self):
        self.assertEqual(self.product.category, self.category)
        with self.assertRaises(ProtectedError):
            self.category.delete()
