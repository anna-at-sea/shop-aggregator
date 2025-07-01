from django.contrib import admin

from .models import Product


@admin.register(Product)
class CustomProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "seller__store_name",
        "origin_city",
        "category",
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
    list_filter = (
        "is_active",
        "category",
        "origin_city",
        "delivery_cities"
    )
    ordering = ("date_added",)
