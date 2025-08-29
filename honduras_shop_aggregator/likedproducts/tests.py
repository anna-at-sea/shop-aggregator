from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse

from honduras_shop_aggregator.likedproducts.models import LikedProduct
from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase


class TestLikesToggle(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.product = Product.objects.get(pk=1)

    def test_create_like(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            LikedProduct.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_remove_like(self):
        self.login_user(self.user)
        self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product.pk})
        )
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            LikedProduct.objects.filter(user=self.user, product=self.product).exists()
        )

    def test_csrf_protection(self):
        self.client = Client(enforce_csrf_checks=True)
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product.pk})
        )
        self.assertEqual(response.status_code, 403)


class TestLikesVisibility(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.product1 = Product.objects.get(pk=1)
        self.product2 = Product.objects.get(pk=4)
        self.product3 = Product.objects.get(pk=5)  # different category

    def test_likes_in_user_profile(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product1.pk})
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product2.pk})
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse('user_profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.product_name)
        self.assertContains(response, self.product2.product_name)
        self.assertNotContains(response, self.product3.product_name)

    def test_likes_in_anonymous_profile(self):
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product3.pk})
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('anonymous_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.product1.product_name)
        self.assertNotContains(response, self.product2.product_name)
        self.assertContains(response, self.product3.product_name)

    def test_likes_in_product_list(self):
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product1.pk})
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        heart_1 = soup.find('button', {'data-product-id': str(self.product1.pk)})
        heart_2 = soup.find('button', {'data-product-id': str(self.product2.pk)})
        heart_3 = soup.find('button', {'data-product-id': str(self.product3.pk)})
        self.assertIn('❤️', heart_1.text)
        self.assertIn('🤍', heart_2.text)
        self.assertIn('🤍', heart_3.text)

    def test_likes_in_category_list(self):
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product2.pk})
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse('category_page', kwargs={'slug': self.product1.category.slug})
        )
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        heart_1 = soup.find('button', {'data-product-id': str(self.product1.pk)})
        heart_2 = soup.find('button', {'data-product-id': str(self.product2.pk)})
        self.assertIn('🤍', heart_1.text)
        self.assertIn('❤️', heart_2.text)

    def test_like_on_product_page(self):
        self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product1.pk})
        )
        response = self.client.get(
            reverse('product_card', kwargs={'slug': self.product1.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-test-id="liked">❤️')
        self.assertNotContains(response, 'data-test-id="unliked">🤍')
        self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product1.pk})
        )
        response = self.client.get(
            reverse('product_card', kwargs={'slug': self.product1.slug})
        )
        self.assertContains(response, 'data-test-id="unliked">🤍')
        self.assertNotContains(response, 'data-test-id="liked">❤️')


class TestLikesMerge(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.product1 = Product.objects.get(pk=1)
        self.product2 = Product.objects.get(pk=2)
        self.product3 = Product.objects.get(pk=3)

    def test_likes_merge_on_login(self):
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product2.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.login_user(self.user)
        response = self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product3.pk})
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse('user_profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.product1.product_name)
        self.assertContains(response, self.product2.product_name)
        self.assertContains(response, self.product3.product_name)


class TestLikesCleanup(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.product = Product.objects.get(pk=1)

    def test_cascade_delete_when_product_deleted(self):
        self.login_user(self.user)
        self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product.pk})
        )
        self.assertTrue(
            LikedProduct.objects.filter(user=self.user, product=self.product).exists()
        )
        self.product.delete()
        self.assertFalse(LikedProduct.objects.filter(user=self.user).exists())

    def test_cascade_delete_when_user_deleted(self):
        self.login_user(self.user)
        self.client.post(
            reverse('toggle_like', kwargs={'product_pk': self.product.pk})
        )
        self.assertTrue(
            LikedProduct.objects.filter(user=self.user, product=self.product).exists()
        )
        self.user.delete()
        self.assertFalse(LikedProduct.objects.filter(product=self.product).exists())


class TestLikesSessionSecurity(BaseTestCase):

    def setUp(self):
        self.product1 = Product.objects.get(pk=1)
        self.product2 = Product.objects.get(pk=2)

    def test_anonymous_likes_isolated_per_session(self):
        other_client = Client()
        self.client.post(
            reverse("toggle_like", kwargs={"product_pk": self.product1.pk})
        )
        other_client.post(
            reverse("toggle_like", kwargs={"product_pk": self.product2.pk})
        )
        response_a = self.client.get(reverse("anonymous_profile"))
        self.assertContains(response_a, self.product1.product_name)
        self.assertNotContains(response_a, self.product2.product_name)
        response_b = other_client.get(reverse("anonymous_profile"))
        self.assertContains(response_b, self.product2.product_name)
        self.assertNotContains(response_b, self.product1.product_name)
