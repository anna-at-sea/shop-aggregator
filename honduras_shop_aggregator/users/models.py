from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from honduras_shop_aggregator.cities.models import City


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

    @property
    def is_seller(self):
        return hasattr(self, 'seller')

    def __str__(self):
        return self.username
