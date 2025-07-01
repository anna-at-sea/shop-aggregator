from django.db import models
from django.utils.translation import gettext_lazy as _


class City(models.Model):

    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"

    name = models.CharField(
        _("City Name"),
        blank=False,
        unique=True,
        max_length=100
    )

    def __str__(self):
        return self.name
