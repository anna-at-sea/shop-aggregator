from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import User


class UserCreateForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'preferred_delivery_city',
            'password1',
            'password2'
        ]

class UserUpdateForm(forms.ModelForm):
    password_confirm = forms.CharField(
        label=_("Enter password to apply changes"),
        widget=forms.PasswordInput,
        required=True
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'preferred_delivery_city'
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password_confirm')
        if not authenticate(
            request=self.request, username=self.instance.username, password=password
        ):
            raise forms.ValidationError(_("Incorrect password."))
        return password


class UserDeleteForm(forms.ModelForm):
    password_confirm = forms.CharField(
        label=_("Enter password to confirm account deletion"),
        widget=forms.PasswordInput,
        required=True
    )

    class Meta:
        model = User
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password_confirm')
        if not authenticate(
            request=self.request, username=self.request.user.username, password=password
        ):
            raise forms.ValidationError(_("Incorrect password."))
        return password


class EmailOrUsernameAuthenticationForm(AuthenticationForm):

    username = forms.CharField(label=_("Username or Email"))

    def clean(self):
        username_or_email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username_or_email and password:
            user = authenticate(
                self.request, username=username_or_email, password=password
            )
            if user is None:
                UserModel = get_user_model()
                try:
                    user_obj = UserModel.objects.get(email__iexact=username_or_email)
                    user = authenticate(
                        self.request, username=user_obj.username, password=password
                    )
                except UserModel.DoesNotExist:
                    pass
            if user is None:
                raise forms.ValidationError(_("Invalid username/email or password"))
            self.confirm_login_allowed(user)
            self.user_cache = user
        return self.cleaned_data
