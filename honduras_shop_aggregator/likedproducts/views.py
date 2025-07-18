from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from honduras_shop_aggregator.likedproducts.models import LikedProduct
from honduras_shop_aggregator.products.models import Product


class ToggleLikeView(View):

    def post(self, request, product_pk):
        product = get_object_or_404(Product, pk=product_pk)
        if request.user.is_authenticated:
            like, created = LikedProduct.objects.get_or_create(
                user=request.user,
                product=product
            )
            if not created:
                like.delete()
                status = 'unliked'
            else:
                status = 'liked'
        else:
            liked_products = request.session.get('liked_products', [])
            if product_pk in liked_products:
                liked_products.remove(product_pk)
                status = 'unliked'
            else:
                liked_products.append(product_pk)
                status = 'liked'
            request.session['liked_products'] = liked_products
        return JsonResponse({'status': status})
