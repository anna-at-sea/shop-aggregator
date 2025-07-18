from django.apps import AppConfig


class LikedproductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'honduras_shop_aggregator.likedproducts'

    def ready(self):
        import honduras_shop_aggregator.likedproducts.signals  # noqa: F401
