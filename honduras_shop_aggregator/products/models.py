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
        User, blank=True, verbose_name=_("Users_liked")
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
        unique=True,
        error_messages={
            "unique": _("This product is already listed.")
        },
        help_text=_("Start with http:// or https://")
    )
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(
        _("description"),
        blank=True,
        help_text=_("Description of the product.")
    )
    date_added = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
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
        super().save(*args, **kwargs)

        if self.image:
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

    def clean(self):
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
