from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from honduras_shop_aggregator.users.models import User


class HttpsURLField(models.URLField):
    def formfield(self, **kwargs):
        defaults = {'form_class': forms.URLField, 'assume_scheme': 'https'}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class Seller(models.Model):

    class Meta:
        verbose_name = "Seller"

    user = models.OneToOneField(
        User, on_delete=models.PROTECT, related_name='seller'
    )
    store_name = models.CharField(
        _("store name"),
        blank=False,
        unique=True,
        error_messages={
            "unique": _("A store with that name already exists.")
        },
        max_length=255
    )
    website = HttpsURLField(
        _("website"),
        blank=False,
        unique=True,
        error_messages={
            "unique": _("A store with that website already exists.")
        },
        help_text=_("Start with http:// or https://")
    )
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("A short description of your store.")
    )
    is_verified = models.BooleanField(default=False)
    date_registered = models.DateTimeField(default=timezone.now)

    def clean(self):
        if self.pk:
            original = Seller.objects.get(pk=self.pk)
            if self.website != original.website:
                raise ValidationError(
                    _("You cannot change your store website.")
                )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.store_name
