import os

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from PIL import Image

from honduras_shop_aggregator.image_utils import (image_upload_path,
                                                  validate_image)
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
    image = models.ImageField(
        upload_to=image_upload_path,
        validators=[validate_image],
        blank=True,
        null=True,
        help_text=_("Upload JPEG or PNG image up to 15MB.")
    )

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

        old_image_path = None
        old_image_name = None
        if self.pk:
            try:
                old = Seller.objects.get(pk=self.pk)
                old_image_name = old.image.name
                if (
                    old.image
                    and old.image != self.image
                    and old.image.name != 'sellers/placeholder.jpg'
                ):
                    old_image_path = old.image.path
            except User.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if (
            self.image
            and self.image.name != 'sellers/placeholder.jpg'
            and self.image.name != old_image_name
        ):
            try:
                img_path = self.image.path
                if not os.path.exists(img_path):
                    return
                img = Image.open(img_path)
                output_size = (240, 240)
                width, height = img.size
                min_side = min(width, height)
                left = (width - min_side) / 2
                top = (height - min_side) / 2
                right = (width + min_side) / 2
                bottom = (height + min_side) / 2
                img = img.crop((left, top, right, bottom))
                img = img.resize(output_size, Image.Resampling.LANCZOS)
                img.save(img_path)
                if old_image_path and os.path.exists(old_image_path):
                    os.remove(old_image_path)
            except Exception as e:
                raise ValidationError(_("Image processing failed") + f": {e}")

    def __str__(self):
        return self.store_name
