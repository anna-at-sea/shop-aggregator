from django.contrib import admin

from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


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
        "seller__store_name",
        "category",
        "origin_city",
        "delivery_cities"
    )
    ordering = ("date_added",)
    inlines = [ProductImageInline]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "order",
    )
    ordering = (
        "product",
        "order",
    )
