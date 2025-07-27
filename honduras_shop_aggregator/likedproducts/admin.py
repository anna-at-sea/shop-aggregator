from django.contrib import admin

from .models import LikedProduct


@admin.register(LikedProduct)
class LikedProductAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__product_name')
    readonly_fields = ('user', 'product', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
