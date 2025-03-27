from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):

    class Meta:
        verbose_name = "User"

    email = models.EmailField(
        _("email address"), blank=False, unique=True,
        error_messages={
            "unique": _("A user with that email already exists.")
        },
    )    

    def __str__(self):
        return self.username
