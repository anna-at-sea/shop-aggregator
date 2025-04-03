# import json
# from os.path import join

from django.contrib import auth
from django.urls import reverse
from django.utils.translation import gettext as _

from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase

FIXTURE_PATH = 'honduras_shop_aggregator/fixtures/'

class TestAuthentication(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()

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


class TestUserProfileRead(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()

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
