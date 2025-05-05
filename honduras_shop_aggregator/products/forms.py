from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.contrib.auth import authenticate
from django.forms.widgets import FileInput
from django.utils.translation import gettext_lazy as _

from .models import Product


class ProductCreateForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            'product_name',
            'product_link',
            'product_price',
            'description',
            'is_active',
            'stock_quantity'
        ]


class ProductImageUpdateForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = ['image']
        widgets = {
            'image': FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('image', label_class='visually-hidden'),
        )


class ProductUpdateForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = [
            'product_name',
            'product_link',
            'product_price',
            'description',
            'is_active',
            'stock_quantity'
        ]


class ProductDeleteForm(forms.ModelForm):
    password_confirm = forms.CharField(
        label=_("Enter store owner's account password to confirm store deletion"),
        widget=forms.PasswordInput,
        required=True
    )

    class Meta:
        model = Product
        fields = []

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password_confirm')
        if not authenticate(
            request=self.request,
            username=self.request.user.username,
            password=password
        ):
            raise forms.ValidationError(_("Incorrect password."))
        return password
