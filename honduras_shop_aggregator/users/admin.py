from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "preferred_delivery_city",
        "seller"
    )
    search_fields = ("username", "email")
    list_filter = ("is_active", "email_verified",)
    ordering = ("date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        (
            None,
            {
                "fields": (
                    "email_verified",
                ),
            },
        ),
    )