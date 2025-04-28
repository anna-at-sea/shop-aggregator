from django.contrib import admin

from .models import Product


@admin.register(Product)
class CustomProductAdmin(admin.ModelAdmin):
    list_display = (
        "seller__store_name",
        "product_name",
        "product_link",
        "product_price",
        "description",
        "is_active",
        "stock_quantity",
        "slug",
        "image"
    )
    search_fields = (
        "seller__store_name",
        "product_name",
        "product_link",
        "description"
    )
    list_filter = ("is_active",)
    ordering = ("date_added",)
