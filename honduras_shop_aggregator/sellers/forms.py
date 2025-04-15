from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from .models import Seller


class SellerCreateForm(forms.ModelForm):

    class Meta:
        model = Seller
        fields = [
            'store_name',
            'website'
        ]


class SellerUpdateForm(forms.ModelForm):
    password_confirm = forms.CharField(
        label=_("Enter store owner's account password to apply changes"),
        widget=forms.PasswordInput,
        required=True
    )

    class Meta:
        model = Seller
        fields = ['store_name', 'website']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password_confirm')
        if not authenticate(
            request=self.request,
            username=self.instance.user.username,
            password=password
        ):
            raise forms.ValidationError(_("Incorrect password."))
        return password


class SellerDeleteForm(forms.ModelForm):
    password_confirm = forms.CharField(
        label=_("Enter store owner's account password to confirm store deletion"),
        widget=forms.PasswordInput,
        required=True
    )

    class Meta:
        model = Seller
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password_confirm')
        if not authenticate(
            request=self.request,
            username=self.request.seller.user.username,
            password=password
        ):
            raise forms.ValidationError(_("Incorrect password."))
        return password
