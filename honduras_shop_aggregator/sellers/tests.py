import json
from os.path import join

from django.urls import reverse
from django.utils.translation import gettext as _

from honduras_shop_aggregator.sellers.models import Seller
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase

FIXTURE_PATH = 'honduras_shop_aggregator/fixtures/'

class TestSellerProfileRead(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.all().first()
        self.user = User.objects.get(pk=self.seller.user.pk)

    def test_read_profile_unauthorized(self):
        response = self.client.get(reverse(
            'seller_profile', kwargs={'store_name': self.seller.store_name}),
            follow=True
        )
        self.assertRedirectWithMessage(response)

    def test_read_own_profile_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'seller_profile', kwargs={'store_name': self.seller.store_name}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_read_other_profile_authorized(self):
        self.other_seller = Seller.objects.get(pk=2)
        self.login_user(self.user)
        response = self.client.get(reverse(
            'seller_profile', kwargs={'store_name': self.other_seller.store_name}),
            follow=True
        )
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You don&#x27;t have permission to access other store profile.")
        )


class TestSellerCreate(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.all().first()
        self.user = User.objects.get(pk=self.seller.user.pk)
        self.user_without_store = User.objects.all().first()
        with open(join(FIXTURE_PATH, "sellers_test_data.json")) as f:
            self.sellers_data = json.load(f)
        self.complete_seller_data = self.sellers_data.get("create_complete")
        self.missing_field_seller_data = self.sellers_data.get(
            "create_missing_field"
        )
        self.duplicate_store_name_data = self.sellers_data.get(
            "create_duplicate_store_name"
        )
        self.duplicate_website_data = self.sellers_data.get("create_duplicate_website")

    def test_create_seller_success(self):
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.complete_seller_data, follow=True
        )
        new_seller = Seller.objects.get(store_name='complete_seller')
        self.assertIsNotNone(new_seller)
        self.assertTrue(Seller.objects.filter(store_name="complete_seller").exists())
        self.assertFalse(new_seller.is_verified)
        self.assertEqual(new_seller.user, self.user_without_store)
        self.assertRedirectWithMessage(
            response,
            'user_profile',
            _("Store is registered and awaiting verification"),
            {'username': self.user_without_store.username}
        )

    def test_create_seller_unauthorized(self):
        response = self.client.post(
            reverse('seller_create'), self.complete_seller_data, follow=True
        )
        self.assertRedirectWithMessage(response)

    def test_create_seller_missing_field(self):
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.missing_field_seller_data
        )
        form = response.context['form']
        self.assertFormError(form, 'website', _('This field is required.'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Seller.objects.filter(store_name="missing_field_seller").exists()
        )

    def test_create_duplicate_store_name(self):
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.duplicate_store_name_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'store_name', _('A store with that name already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_website(self):
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.duplicate_website_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'website', _('A store with that website already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_user_seller(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_create'), self.complete_seller_data, follow=True
        )
        self.assertFalse(Seller.objects.filter(store_name="complete_seller").exists())
        self.assertEqual(self.seller.user, self.user)
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _(
                "You already have a store associated with your account. "
                "Each user can register only one store. "
                "If you wish to create another store, "
                "please log in with a different account or register a new one."
            ),
            {'store_name': self.user.seller.store_name}
        )


class TestSellerUpdate(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.all().first()
        self.user = User.objects.get(pk=self.seller.user.pk)
        with open(join(FIXTURE_PATH, "sellers_test_data.json")) as f:
            self.sellers_data = json.load(f)
        self.complete_seller_data = self.sellers_data.get("update_complete")
        self.missing_field_seller_data = self.sellers_data.get(
            "update_missing_field"
        )
        self.duplicate_store_name_data = self.sellers_data.get(
            "update_duplicate_store_name"
        )
        self.duplicate_website_data = self.sellers_data.get("update_duplicate_website")
        self.change_user_attempt_data = self.sellers_data.get("change_user_attempt")

    def test_update_seller_success(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.complete_seller_data, follow=True
        )
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.store_name, 'new_store_name')
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _("Store is updated successfully"),
            {'store_name': self.seller.store_name}
        )

    def test_impossible_to_change_user(self):
        self.login_user(self.user)
        self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.change_user_attempt_data
        )
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.user, self.user)

    def test_update_seller_missing_field(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.missing_field_seller_data
        )
        form = response.context['form']
        self.assertFormError(form, 'website', _('This field is required.'))
        self.assertEqual(response.status_code, 200)

    def test_update_duplicate_store_name(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.duplicate_store_name_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'store_name', _('A store with that name already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_update_duplicate_website(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.duplicate_website_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'website', _('A store with that website already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_update_other_seller(self):
        self.other_seller = Seller.objects.get(pk=2)
        self.login_user(self.user)
        response = self.client.get(
            reverse('seller_update',
            kwargs={'store_name': self.other_seller.store_name}),
            follow=True
        )
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to access other store profile.")
        )

    def test_update_seller_unauthorized(self):
        response = self.client.get(
            reverse(
                'seller_update',
                kwargs={'store_name': self.seller.store_name}
            ), follow=True
        )
        self.assertRedirectWithMessage(response)


class TestSellerDelete(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.all().first()
        self.seller_with_product = Seller.objects.get(pk=3)
        self.user = User.objects.get(pk=self.seller.user.pk)
        self.user_with_seller_with_product = User.objects.get(
            pk=self.seller_with_product.user.pk
        )

    def test_delete_seller_success(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.assertFalse(Seller.objects.filter(pk=1).exists())
        self.assertTrue(User.objects.filter(pk=3).exists())
        self.assertRedirectWithMessage(
            response, 'index', _("Store deleted successfully")
        )

    def test_delete_seller_unauthorized(self):
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.assertTrue(Seller.objects.filter(pk=1).exists())
        self.assertRedirectWithMessage(response)

    def test_delete_seller_wrong_password(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller.store_name}
            ), {'password_confirm': 'wrong_password'}, follow=True
        )
        self.assertTrue(Seller.objects.filter(pk=1).exists())
        form = response.context['form']
        self.assertFormError(
            form, 'password_confirm', _("Incorrect password.")
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_other_seller(self):
        self.login_user(self.user)
        self.other_seller = Seller.objects.get(pk=2)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.other_seller.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.assertTrue(Seller.objects.filter(pk=2).exists())
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to access other store profile.")
        )

    def test_delete_seller_with_product(self):
        self.login_user(self.user_with_seller_with_product)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller_with_product.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.assertTrue(Seller.objects.filter(pk=3).exists())
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _("This store still has active products and cannot be deleted"),
            {'store_name': self.seller_with_product.store_name}
        )
