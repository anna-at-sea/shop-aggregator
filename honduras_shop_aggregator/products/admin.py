from django.contrib import admin

from .models import Product


@admin.register(Product)
class CustomProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "is_deleted",
        "deleted_at",
        "seller__store_name",
        "origin_city",
        "category",
        "product_link",
        "product_price",
        "is_active",
        "stock_quantity"
    )
    search_fields = (
        "seller__store_name",
        "product_name",
        "product_link",
        "description"        
    )
    list_filter = (
        "is_deleted",
        "is_active",
        "category",
        "origin_city",
        "delivery_cities"
    )
    ordering = ("date_added",)
