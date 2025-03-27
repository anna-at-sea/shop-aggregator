from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext as _

from .models import User


class UserCreateForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
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
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password_confirm')
        if not authenticate(request=self.request, username=self.instance.username, password=password):
            raise forms.ValidationError("Incorrect password.")
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
        if not authenticate(request=self.request, username=self.request.user.username, password=password):
            raise forms.ValidationError("Incorrect password.")
        return password
