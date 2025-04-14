from django.contrib import admin

from .models import Seller


@admin.register(Seller)
class CustomSellerAdmin(admin.ModelAdmin):
    list_display = ("store_name", "website", "user__username", "is_verified")
    search_fields = ("store_name", "website", "user__email")
    list_filter = ("is_verified",)
    ordering = ("date_registered",)
