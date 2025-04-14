from django import forms

from .models import Seller

# from django.contrib.auth import authenticate
# from django.utils.translation import gettext_lazy as _


class SellerCreateForm(forms.ModelForm):

    class Meta:
        model = Seller
        fields = [
            'store_name',
            'website'
        ]
