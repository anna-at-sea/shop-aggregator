from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
# from django.contrib.auth import authenticate
# from django.utils.translation import gettext_lazy as _
from django.forms.widgets import FileInput

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
