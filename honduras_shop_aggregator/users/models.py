import os

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image

from honduras_shop_aggregator.cities.models import City
from honduras_shop_aggregator.image_utils import (image_upload_path,
                                                  validate_image)


class User(AbstractUser):

    class Meta:
        verbose_name = "User"

    email = models.EmailField(
        _("email address"), blank=False, unique=True,
        error_messages={
            "unique": _("A user with that email already exists.")
        },
    )
    preferred_delivery_city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="connected_users",
        blank=True,
        null=True
    )
    image = models.ImageField(
        upload_to=image_upload_path,
        validators=[validate_image],
        blank=True,
        null=True,
        help_text=_("Upload JPEG or PNG image up to 15MB.")
    )

    @property
    def is_seller(self):
        return hasattr(self, 'seller')

    def save(self, *args, **kwargs):
        old_image_path = None
        old_image_name = None
        if self.pk:
            try:
                old = User.objects.get(pk=self.pk)
                old_image_name = old.image.name
                if (
                    old.image
                    and old.image != self.image
                    and old.image.name != 'users/placeholder.jpg'
                ):
                    old_image_path = old.image.path
            except User.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if (
            self.image
            and self.image.name != 'users/placeholder.jpg'
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
        return self.username
