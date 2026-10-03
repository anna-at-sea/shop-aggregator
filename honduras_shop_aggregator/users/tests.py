import json
import os
import tempfile
from os.path import join

from django.contrib import auth
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _
from PIL import Image

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.cities.models import City
from honduras_shop_aggregator.likedproducts.models import LikedProduct
from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.sellers.models import Seller
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.users.views import (AnonymousProfileView,
                                                  UserProfileView)
from honduras_shop_aggregator.utils import BaseTestCase

FIXTURE_PATH = 'honduras_shop_aggregator/fixtures/'
IMAGE_PATH = 'honduras_shop_aggregator/static/images'
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

class TestAuthentication(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_login(self):
        login_successful = self.client.login(
            username=self.user.username,
            password="correct_password"
        )
        self.assertTrue(login_successful, _("User login failed"))
        login_unsuccessful = self.client.login(
            username=self.user.username,
            password="wrong_password"
        )
        self.assertFalse(
            login_unsuccessful, _("User login should have failed but it passed")
        )

    def test_login_redirect(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.username,
            "password": "correct_password"
        }, follow=True)
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You are logged in")
        )

    def test_login_with_email(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.email,
            "password": "correct_password"
        }, follow=True)
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You are logged in")
        )

    def test_logout(self):
        self.login_user(self.user)
        self.client.logout()
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated, _("User should be logged out"))
        

    def test_logout_redirect(self):
        self.login_user(self.user)
        response = self.client.post(reverse("logout"), follow=True)
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You are logged out")
        )
        response = self.client.get(
            reverse('user_update', kwargs={'username': self.user.username}),
            follow=True
        )
        self.assertRedirectWithMessage(response)


class TestPasswordReset(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_password_reset_page(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Forgot your password?"))

    def test_password_reset_sends_email(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": self.user.email},
        )
        self.assertRedirects(
            response,
            reverse("password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.user.email])
        self.assertIn("Cangrejal", email.body)
        self.assertIn(_("password"), email.subject.lower())

    def test_password_reset_unknown_email_does_not_send_email(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "doesnotexist@example.com"},
        )
        self.assertRedirects(
            response,
            reverse("password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_changes_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse(
            "password_reset_confirm",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        reset_url = response.url
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reset_url,
            {
                "new_password1": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
        )
        self.assertRedirects(
            response,
            reverse("password_reset_complete"),
        )
        self.user.refresh_from_db()
        self.assertTrue(
            self.user.check_password("NewStrongPassword123!")
        )

    def test_password_reset_token_cannot_be_reused(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse(
            "password_reset_confirm",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        reset_url = response.url
        response = self.client.get(reset_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reset_url,
            {
                "new_password1": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
        )
        self.assertRedirects(
            response,
            reverse("password_reset_complete"),
        )
        # The same token should no longer be valid.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Invalid reset link"))


class TestEmailVerification(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def get_verification_url(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        return reverse(
            "email_verification_confirm",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )

    def test_verification_sent_page(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse("email_verification_sent")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _("Check your email")
        )
        self.assertContains(
            response,
            _("We've sent a verification link to your email address.")
        )
        self.assertNotContains(
            response,
            _("You can still log in and use your account without verifying your email.")
        )

    def test_registration_sends_verification_email(self):
        data = {
            "first_name": "Test",
            "last_name": "User",
            "username": "verification_user",
            "email": "verification@example.com",
            "password1": "correct_password123!",
            "password2": "correct_password123!",
        }
        response = self.client.post(
            reverse("user_create"),
            data,
            follow=True,
        )
        user = User.objects.get(
            username="verification_user"
        )
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to,
            ["verification@example.com"],
        )
        self.assertIn(
            _("Verify your Cangrejal email address"),
            mail.outbox[0].subject,
        )
        self.assertContains(
            response,
            _("Check your email")
        )
        self.assertContains(
            response,
            _("You can still log in and use your account without verifying your email.")
        )

    def test_valid_verification_token_verifies_email(self):
        url = self.get_verification_url()
        response = self.client.get(url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertRedirects(
            response,
            reverse("login"),
        )

    def test_valid_verification_token_redirects_logged_in_user_to_profile(self):
        self.login_user(self.user)
        self.user.refresh_from_db()
        url = self.get_verification_url()
        response = self.client.get(url, follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertRedirects(
            response,
            reverse(
                "user_profile",
                kwargs={"username": self.user.username},
            ),
        )

    def test_invalid_verification_token(self):
        url = reverse(
            "email_verification_confirm",
            kwargs={
                "uidb64": urlsafe_base64_encode(
                    force_bytes(self.user.pk)
                ),
                "token": "invalid-token",
            },
        )
        response = self.client.get(url)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _("Invalid verification link"),
        )

    def test_already_verified_email(self):
        self.user.email_verified = True
        self.user.save()
        self.login_user(self.user)
        url = self.get_verification_url()
        response = self.client.get(url, follow=True)
        self.assertRedirectWithMessage(
            response,
            "user_profile",
            _("Your email address is already verified."),
            {"username": self.user.username},
        )

    def test_resend_verification_email(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse("email_verification_resend"),
            follow=True,
        )
        self.assertRedirectWithMessage(
            response,
            "email_verification_sent",
            _("A new verification email has been sent."),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to,
            [self.user.email],
        )

    def test_verified_user_cannot_resend_verification_email(self):
        self.user.email_verified = True
        self.user.save()
        self.login_user(self.user)
        response = self.client.get(
            reverse("email_verification_resend"),
            follow=True,
        )
        self.assertRedirectWithMessage(
            response,
            "user_profile",
            _("Your email address is already verified."),
            {"username": self.user.username},
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verification_requires_login(self):
        response = self.client.get(
            reverse("email_verification_resend"),
            follow=True,
        )
        self.assertRedirectWithMessage(response)


class TestUserProfileRead(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_read_profile_unauthorized(self):
        response = self.client.get(reverse(
            'user_profile', kwargs={'username': self.user.username}),
            follow=True
        )
        self.assertRedirectWithMessage(response)

    def test_read_own_profile_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'user_profile', kwargs={'username': self.user.username}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_read_other_profile_authorized(self):
        self.other_user = User.objects.get(pk=2)
        self.login_user(self.user)
        response = self.client.get(reverse(
            'user_profile', kwargs={'username': self.other_user.username}),
            follow=True
        )
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You don&#x27;t have permission to view or edit other user.")
        )

    def test_read_nonexistent(self):
        response = self.client.get('/wrong_url/')
        self.assertEqual(response.status_code, 404)

    def test_unverified_user_sees_email_verification_warning(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "user_profile",
                kwargs={"username": self.user.username},
            )
        )
        self.assertContains(
            response,
            _("Your email address is not verified."),
        )
        self.assertContains(
            response,
            _("Resend verification email"),
        )

    def test_verified_user_does_not_see_email_verification_warning(self):
        self.user.email_verified = True
        self.user.save()
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "user_profile",
                kwargs={"username": self.user.username},
            )
        )
        self.assertNotContains(
            response,
            _("Your email address is not verified."),
        )
        self.assertNotContains(
            response,
            _("Resend verification email"),
        )


class TestUserProfileProducts(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.paginate_by = UserProfileView.paginate_by
        self.login_user(self.user)
        self.seller = Seller.objects.get(pk=3)
        self.category = Category.objects.get(pk=1)
        self.city = City.objects.get(pk=1)

    def create_and_like_products(self, count, user=None):
        user = user or self.user
        products = []
        for i in range(count):
            product = Product.objects.create(
                product_name=f"Profile Product {i}",
                product_price=10 + i,
                stock_quantity=5,
                seller=self.seller,
                category=self.category,
                origin_city=self.city,
            )
            LikedProduct.objects.create(
                user=user,
                product=product,
            )
            products.append(product)
        return products

    def test_load_more_pages_do_not_overlap(self):
        self.create_and_like_products(self.paginate_by + 5)
        url = reverse(
            "user_profile",
            kwargs={"username": self.user.username},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        page_1_ids = {
            product.pk
            for product in response.context["products"]
        }
        response = self.client.get(url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        page_2_ids = {
            product.pk
            for product in response.context["products"]
        }
        self.assertTrue(
            page_1_ids.isdisjoint(page_2_ids)
        )

    def test_load_more_button_visibility(self):
        self.create_and_like_products(self.paginate_by + 5)
        url = reverse(
            "user_profile",
            kwargs={"username": self.user.username},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Load More"))
        last_page = response.context["page_obj"].paginator.num_pages
        response = self.client.get(url, {"page": last_page})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, _("Load More"))

    def test_ajax_load_more_response(self):
        self.create_and_like_products(self.paginate_by + 5)
        url = reverse(
            "user_profile",
            kwargs={"username": self.user.username},
        )
        response = self.client.get(
            url,
            {"page": 2},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("products_html", data)
        self.assertIn("has_next", data)
        self.assertIn("next_page", data)


class TestAnonymousProfileProducts(BaseTestCase):

    def setUp(self):
        self.paginate_by = AnonymousProfileView.paginate_by
        self.seller = Seller.objects.get(pk=3)
        self.category = Category.objects.get(pk=1)
        self.city = City.objects.get(pk=1)

    def create_liked_products(self, count):
        products = []
        for i in range(count):
            product = Product.objects.create(
                product_name=f"Anonymous Product {i}",
                product_price=10 + i,
                stock_quantity=5,
                seller=self.seller,
                category=self.category,
                origin_city=self.city,
            )
            products.append(product)
        session = self.client.session
        session["liked_products"] = [
            product.pk for product in products
        ]
        session.save()
        return products

    def test_load_more_pages_do_not_overlap(self):
        self.create_liked_products(self.paginate_by + 5)
        url = reverse("anonymous_profile")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        page_1_ids = {
            product.pk
            for product in response.context["products"]
        }
        response = self.client.get(url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        page_2_ids = {
            product.pk
            for product in response.context["products"]
        }
        self.assertTrue(
            page_1_ids.isdisjoint(page_2_ids)
        )

    def test_liked_products_are_ordered_newest_first(self):
        count = 3
        products = self.create_liked_products(count)
        response = self.client.get(reverse("anonymous_profile"))
        self.assertEqual(response.status_code, 200)
        product_ids = [
            product.pk
            for product in response.context["products"]
        ]
        self.assertEqual(
            product_ids[:3],
            [products[count-1].pk, products[count-2].pk, products[count-3].pk],
        )

    def test_load_more_button_visibility(self):
        self.create_liked_products(self.paginate_by + 5)
        url = reverse("anonymous_profile")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Load More"))
        last_page = response.context["page_obj"].paginator.num_pages
        response = self.client.get(url, {"page": last_page})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, _("Load More"))

    def test_ajax_load_more_response(self):
        self.create_liked_products(self.paginate_by + 5)
        url = reverse("anonymous_profile")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        last_page = response.context["page_obj"].paginator.num_pages
        response = self.client.get(
            url,
            {"page": last_page},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("products_html", data)
        self.assertIn("has_next", data)
        self.assertIn("next_page", data)
        self.assertFalse(data["has_next"])
        self.assertIsNone(data["next_page"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestUserCreate(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        with open(join(FIXTURE_PATH, "users_test_data.json")) as f:
            self.users_data = json.load(f)
        self.complete_user_data = self.users_data.get("create_complete")
        self.missing_field_user_data = self.users_data.get(
            "create_missing_field"
        )
        self.duplicate_username_data = self.users_data.get("create_duplicate_username")
        self.duplicate_email_data = self.users_data.get("create_duplicate_email")
        with open(os.path.join(IMAGE_PATH, "test_img_to_crop.jpg"), 'rb') as img_file:
            self.success_image = SimpleUploadedFile(
                name='test_image_to_crop.jpg',
                content=img_file.read(),
                content_type='image/jpeg'
            )
        with open(os.path.join(IMAGE_PATH, "test_img_new.jpg"), 'rb') as img_file:
            self.new_image = SimpleUploadedFile(
                name='test_image_new.jpg',
                content=img_file.read(),
                content_type='image/jpeg'
            )

    def test_create_user_success(self):
        response = self.client.post(
            reverse('user_create'), self.complete_user_data, follow=True
        )
        user = User.objects.get(username='complete_user')
        self.assertIsNotNone(user)
        self.assertTrue(User.objects.filter(username="complete_user").exists())
        self.assertRedirectWithMessage(
            response,
            'email_verification_sent',
            _("Your account has been created successfully.")
        )
        user.refresh_from_db()
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)

    def test_create_user_with_profile_picture(self):
        data = self.complete_user_data.copy()
        data['image'] = self.success_image
        response = self.client.post(
            reverse('user_create'),
            data,
            format='multipart',
            follow=True
        )
        user = User.objects.get(username='complete_user')
        self.assertIsNotNone(user)
        self.assertTrue(User.objects.filter(username="complete_user").exists())
        user.refresh_from_db()
        img = Image.open(user.image.path)
        self.assertEqual(img.size, (240, 240))
        self.assertIsNotNone(user.image)
        self.assertEqual(user.image.name, f'users/{user.username}.jpg')
        self.assertRedirectWithMessage(
            response,
            'email_verification_sent',
            _("Your account has been created successfully.")
        )
        user.refresh_from_db()
        self.assertFalse(user.email_verified)
        self.assertEqual(len(mail.outbox), 1)

    def test_replace_or_delete_user_image_deletes_old_file(self):
        data = self.complete_user_data.copy()
        data['image'] = self.success_image
        self.client.post(
            reverse('user_create'),
            data,
            format='multipart',
            follow=True
        )
        user = User.objects.get(username='complete_user')
        old_image_path = user.image.path
        self.assertTrue(os.path.exists(old_image_path))
        self.login_user(user)
        response = self.client.post(
            reverse('user_update', kwargs={'username': user.username}),
            data={
                'image': self.new_image,
                'username': user.username,
                'email': user.email,
                'password_confirm': 'correct_password'
            },
            format='multipart',
            follow=True
        )
        self.assertRedirectWithMessage(
            response,
            'user_profile',
            _("User is updated successfully"),
            {'username': user.username}
        )
        user.refresh_from_db()
        new_image_path = user.image.path
        self.assertNotEqual(new_image_path, old_image_path)
        self.assertTrue(os.path.exists(new_image_path))
        self.assertFalse(os.path.exists(old_image_path))
        response = self.client.post(
            reverse('user_update', kwargs={'username': user.username}),
            data={
                'username': user.username,
                'email': user.email,
                'image-clear': 'on',
                'password_confirm': 'correct_password'
            },
            follow=True
        )
        self.assertRedirectWithMessage(
            response,
            'user_profile',
            _("User is updated successfully"),
            {'username': user.username}
        )
        user.refresh_from_db()
        self.assertFalse(os.path.exists(new_image_path))

    def test_create_user_missing_field(self):
        response = self.client.post(
            reverse('user_create'), self.missing_field_user_data
        )
        form = response.context['form']
        self.assertFormError(form, 'email', _('This field is required.'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username="missing_field_user").exists()
        )

    def test_create_duplicate_username(self):
        response = self.client.post(
            reverse('user_create'), self.duplicate_username_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'username', _('A user with that username already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_email(self):
        response = self.client.post(
            reverse('user_create'), self.duplicate_email_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'email', _('A user with that email already exists.')
        )
        self.assertEqual(response.status_code, 200)


class TestUserUpdate(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        with open(join(FIXTURE_PATH, "users_test_data.json")) as f:
            self.users_data = json.load(f)
        self.complete_user_data = self.users_data.get("update_complete")
        self.missing_field_user_data = self.users_data.get(
            "update_missing_field"
        )
        self.duplicate_username_data = self.users_data.get("update_duplicate_username")
        self.duplicate_email_data = self.users_data.get("update_duplicate_email")

    def test_update_user_success(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_update', kwargs={'username': self.user.username}),
            self.complete_user_data, follow=True
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'new_username')
        self.assertRedirectWithMessage(
            response,
            'user_profile',
            _("User is updated successfully"),
            {'username': self.user.username}
        )

    def test_update_user_missing_field(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_update', kwargs={'username': self.user.username}),
            self.missing_field_user_data
        )
        form = response.context['form']
        self.assertFormError(form, 'email', _('This field is required.'))
        self.assertEqual(response.status_code, 200)

    def test_update_duplicate_username(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_update', kwargs={'username': self.user.username}),
            self.duplicate_username_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'username', _('A user with that username already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_update_duplicate_email(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_update', kwargs={'username': self.user.username}),
            self.duplicate_email_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'email', _('A user with that email already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_update_other_user(self):
        self.other_user = User.objects.get(pk=2)
        self.login_user(self.user)
        response = self.client.get(
            reverse('user_update',
            kwargs={'username': self.other_user.username}),
            follow=True
        )
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to view or edit other user.")
        )

    def test_update_user_unauthorized(self):
        response = self.client.get(
            reverse('user_update', kwargs={'username': self.user.username}), follow=True
        )
        self.assertRedirectWithMessage(response)


class TestPasswordChange(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        with open(join(FIXTURE_PATH, "users_test_data.json")) as f:
            self.users_data = json.load(f)
        testing_cases = [
            "password_correct",
            "password_incorrect",
            "old_password_missing",
            "new_password_missing",
            "new_passwords_not_matching"
        ]
        for case in testing_cases:
            setattr(self, case, self.users_data.get(case))

    def test_change_password_success(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_password_change', kwargs={'username': self.user.username}),
            self.password_correct, follow=True
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new_password'))
        self.assertRedirectWithMessage(
            response,
            'user_profile',
            _("Password is changed successfully"),
            {'username': self.user.username}
        )

    def test_change_password_incorrect(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_password_change', kwargs={'username': self.user.username}),
            self.password_incorrect
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'old_password',
            _("Your old password was entered incorrectly. Please enter it again.")
        )
        self.assertEqual(response.status_code, 200)

    def test_change_password_missing_old(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_password_change', kwargs={'username': self.user.username}),
            self.old_password_missing
        )
        form = response.context['form']
        self.assertFormError(form, 'old_password', _('This field is required.'))
        self.assertEqual(response.status_code, 200)

    def test_change_password_missing_new(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_password_change', kwargs={'username': self.user.username}),
            self.new_password_missing
        )
        form = response.context['form']
        self.assertFormError(form, 'new_password1', _('This field is required.'))
        self.assertEqual(response.status_code, 200)

    def test_change_password_not_matching(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('user_password_change', kwargs={'username': self.user.username}),
            self.new_passwords_not_matching
        )
        form = response.context['form']
        self.assertFormError(
            form, 'new_password2', _("The two password fields didn\u2019t match.")
        )
        self.assertEqual(response.status_code, 200)

    def test_change_password_other_user(self):
        self.other_user = User.objects.get(pk=2)
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                'user_password_change',
                kwargs={'username': self.other_user.username}
            ), follow=True
        )
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to view or edit other user.")
        )

    def test_change_password_unauthorized(self):
        response = self.client.get(
            reverse(
                'user_password_change',
                kwargs={'username': self.user.username}
            ), follow=True
        )
        self.assertRedirectWithMessage(response)


class TestUserSoftDelete(BaseTestCase):

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.user_with_store = User.objects.get(pk=3)

    def test_soft_delete_user_success(self):
        self.login_user(self.user)
        old_email = self.user.email
        response = self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.user.username}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
        self.assertFalse(self.user.is_active)
        self.assertEqual(
            self.user.deleted_email,
            old_email
        )
        self.assertEqual(
            self.user.email,
            f"deleted-{self.user.pk}@deleted.local"
        )
        self.assertRedirectWithMessage(
            response, 'index', _("Account deleted successfully")
        )

    def test_soft_delete_logs_out_user(self):
        self.login_user(self.user)
        self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.user.username}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_deleted_user_cannot_login(self):
        self.user.is_active = False
        self.user.is_deleted = True
        self.user.save()
        success = self.login_user(self.user)
        self.assertFalse(success)

    def test_delete_user_with_store(self):
        self.login_user(self.user_with_store)
        response = self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.user_with_store.username}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.user_with_store.refresh_from_db()
        self.assertFalse(self.user_with_store.is_deleted)
        self.assertTrue(self.user_with_store.is_active)
        self.assertRedirectWithMessage(
            response,
            'user_profile',
            _("This account is linked to a store and cannot be deleted"),
            {'username': self.user_with_store.username}
        )

    def test_delete_user_wrong_password(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.user.username}
            ), {'password_confirm': 'wrong_password'}, follow=True
        )
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_deleted)
        self.assertTrue(self.user.is_active)
        form = response.context['form']
        self.assertFormError(
            form, 'password_confirm', _("Incorrect password.")
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_other_user(self):
        self.login_user(self.user)
        self.other_user = User.objects.get(pk=2)
        response = self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.other_user.username}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.other_user.refresh_from_db()
        self.assertFalse(self.other_user.is_deleted)
        self.assertTrue(self.other_user.is_active)
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to view or edit other user.")
        )

    def test_delete_user_unauthorized(self):
        response = self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.user.username}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.assertRedirectWithMessage(response)
