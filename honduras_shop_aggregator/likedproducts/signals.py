from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from honduras_shop_aggregator.likedproducts.models import LikedProduct
from honduras_shop_aggregator.products.models import Product


@receiver(user_logged_in)
def merge_likes_on_login(sender, request, user, **kwargs):
    session_likes = request.session.get('liked_products', [])
    if session_likes:
        user_likes = set(user.likes.values_list('pk', flat=True))
        new_likes = set(session_likes) - user_likes
        for product_pk in new_likes:
            try:
                product = Product.objects.get(pk=product_pk)
                LikedProduct.objects.get_or_create(user=user, product=product)
            except Product.DoesNotExist:
                pass
        del request.session['liked_products']
        request.session.modified = True
