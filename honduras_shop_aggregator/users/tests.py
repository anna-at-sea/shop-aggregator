import json
from os.path import join

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


class TestUserCreate(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()
        with open(join(FIXTURE_PATH, "users_test_data.json")) as f:
            self.users_data = json.load(f)
        self.complete_user_data = self.users_data.get("create_complete")
        self.missing_field_user_data = self.users_data.get(
            "create_missing_field"
        )
        self.duplicate_username_data = self.users_data.get("create_duplicate_username")
        self.duplicate_email_data = self.users_data.get("create_duplicate_email")

    def test_create_user_success(self):
        response = self.client.post(
            reverse('user_create'), self.complete_user_data, follow=True
        )
        user = User.objects.get(username='complete_user')
        self.assertIsNotNone(user)
        self.assertTrue(User.objects.filter(username="complete_user").exists())
        self.assertRedirectWithMessage(
            response, 'login', _("User is registered successfully")
        )

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
        self.user = User.objects.all().first()
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
        self.user = User.objects.all().first()
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


class TestUserDelete(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()
        self.user_with_store = User.objects.get(pk=3)

    def test_delete_user_success(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.user.username}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.assertFalse(User.objects.filter(pk=1).exists())
        self.assertRedirectWithMessage(
            response, 'index', _("Account deleted successfully")
        )

    def test_delete_user_with_store(self):
        self.login_user(self.user_with_store)
        response = self.client.post(
            reverse(
                'user_delete',
                kwargs={'username': self.user_with_store.username}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.assertTrue(User.objects.filter(pk=3).exists())
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
        self.assertTrue(User.objects.filter(pk=1).exists())
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
        self.assertTrue(User.objects.filter(pk=2).exists())
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
