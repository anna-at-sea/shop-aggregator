from django.contrib import admin

from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.sellers.models import Seller


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ("product_name", "product_price", "is_active", "stock_quantity")
    show_change_link = True


@admin.register(Seller)
class CustomSellerAdmin(admin.ModelAdmin):
    list_display = (
        "store_name", "website", "user__username", "description", "is_verified"
    )
    search_fields = ("store_name", "website", "user__email")
    list_filter = ("is_verified",)
    ordering = ("date_registered",)

    inlines = [ProductInline]
