import os
import re

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from PIL import Image

from honduras_shop_aggregator.sellers.models import Seller
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import image_upload_path, validate_image


class HttpsURLField(models.URLField):
    def formfield(self, **kwargs):
        defaults = {'form_class': forms.URLField, 'assume_scheme': 'https'}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class Product(models.Model):

    class Meta:
        verbose_name = "Product"

    user = models.ManyToManyField(
        User, blank=True, verbose_name="Users_liked"
    )
    seller = models.ForeignKey(
        Seller, related_name="seller_products",
        blank=False, on_delete=models.PROTECT
    )
    product_name = models.CharField(
        _("product name"),
        blank=False,
        unique=False,
        max_length=255
    )
    product_link = HttpsURLField(
        _("product link"),
        blank=True,
        null=True,
        unique=True,
        error_messages={
            "unique": _("This product is already listed.")
        },
        help_text=_("Start with http:// or https://")
    )
    product_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=False
    )
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Description of the product.")
    )
    date_added = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(
        default=0,
        blank=False
    )
    slug = models.SlugField(
        unique=True,
        max_length=255,
        blank=False
    )
    image = models.ImageField(
        upload_to=image_upload_path,
        validators=[validate_image],
        blank=True,
        null=True,
        default='products/placeholder.png',
        help_text=_("Upload JPEG or PNG image up to 2MB.")
    )

    def save(self, *args, **kwargs):

        if not self.slug:
            base_slug = slugify(self.product_name)
            slug = base_slug
            num = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug

        self.full_clean()

        old_image_path = None
        old_image_name = None
        if self.pk:
            try:
                old = Product.objects.get(pk=self.pk)
                old_image_name = old.image.name
                if (
                    old.image
                    and old.image != self.image
                    and old.image.name != 'products/placeholder.png'
                ):
                    old_image_path = old.image.path
            except Product.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if (
            self.image
            and self.image.name != 'products/placeholder.png'
            and self.image.name != old_image_name
        ):
            try:
                img_path = self.image.path
                img = Image.open(img_path)
                output_size = (500, 500)
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

    def clean(self):
        super().clean()

        if self.product_price is not None and self.product_price <= 0:
            raise ValidationError({'product_price': _("Price must be greater than 0.")})

        if self.product_link:
            seller_website = self.seller.website
            if seller_website and not self.product_link.startswith(seller_website):
                raise ValidationError(
                    {
                        'product_link': _(
                            "Product link must start with the seller's website URL."
                        )
                    }
                )

        link_pattern = re.compile(
            r'((http|https):\/\/)?(www\.)?[a-zA-Z0-9\-.]+\.[a-zA-Z]{2,}(\/\S*)?'
        )
        if self.product_name and link_pattern.search(self.product_name):
            raise ValidationError(
                {'product_name': _("Product name cannot contain links.")}
            )
        if self.description and link_pattern.search(self.description):
            raise ValidationError(
                {'description': _("Description cannot contain links.")}
            )

    def __str__(self):
        return self.product_name

# after adding soft deletion (filed is_deleted / date_deleted:
# Remove unique=True from the product_link field,
# add to clean():
# def clean(self):
#     super().clean()
    
#     if self.product_link:
#         existing = Product.objects.filter(
#             product_link=self.product_link,
#             is_deleted=False
#         ).exclude(pk=self.pk)
#         if existing.exists():
#             raise ValidationError({'product_link': _("This product is already .")})
# + add to the flash message that if product is not active then
# you may change is_activesetting or if you want to replace that 
# card with the new one first delete that product
