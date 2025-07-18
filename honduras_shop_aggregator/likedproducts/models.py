from django.db import models

from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.users.models import User


class LikedProduct(models.Model):

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'], name='unique_user_product_like'
            )
        ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} likes {self.product}"
