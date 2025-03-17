from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # list_display = ("username", "email", "is_staff", "date_joined")  # Customize fields shown in the list
    search_fields = ("username", "email")
    list_filter = ("is_staff", "is_active")
    ordering = ("date_joined",)
