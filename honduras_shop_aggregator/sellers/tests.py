import json
import os
import tempfile
from os.path import join

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _
from PIL import Image

from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.sellers.models import Seller
from honduras_shop_aggregator.sellers.views import (PublicSellerProfileView,
                                                    SellerListView,
                                                    SellerProfileView)
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase

FIXTURE_PATH = 'honduras_shop_aggregator/fixtures/'
IMAGE_PATH = 'honduras_shop_aggregator/static/images'
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

class TestPrivateSellerProfileRead(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=3)
        self.user = User.objects.get(pk=self.seller.user.pk)
        self.active_product = Product.objects.get(pk=1)
        self.unavailable_product = Product.objects.get(pk=2)
        self.out_of_stock_product = Product.objects.get(pk=3)
        self.other_seller_product = Product.objects.get(pk=4)

    def create_extra_products(self, count):
        products = []
        for i in range(count):
            product = Product.objects.create(
                product_name=f"Private Profile Product {i}",
                product_price=10 + i,
                stock_quantity=5,
                seller=self.seller,
                category=self.active_product.category,
                origin_city=self.active_product.origin_city,
                is_active=True,
                is_deleted=False,
            )
            products.append(product)
        return products

    def test_read_profile_unauthorized(self):
        response = self.client.get(reverse(
            'seller_profile', kwargs={'store_name': self.seller.store_name}),
            follow=True
        )
        self.assertRedirectWithMessage(response)

    def test_read_own_profile_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'seller_profile', kwargs={'store_name': self.seller.store_name}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_product.product_name)
        self.assertContains(response, self.unavailable_product.product_name)
        self.assertContains(response, self.out_of_stock_product.product_name)
        self.assertNotContains(response, self.other_seller_product.product_name)
        self.assertContains(response, _("Your Products"))
        self.assertContains(response, _("Store Settings"))
        self.assertContains(response, _("Add New Product"))

    def test_read_deleted_profile_authorized(self):
        self.login_user(self.user)
        self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.seller.refresh_from_db()
        response = self.client.get(reverse(
            'seller_profile', kwargs={'store_name': self.seller.store_name}),
            follow=True
        )
        self.assertNotContains(response, self.active_product.product_name)
        self.assertNotContains(response, self.unavailable_product.product_name)
        self.assertNotContains(response, _("Your Products"))
        self.assertNotContains(response, _("Store Settings"))
        self.assertNotContains(response, _("Add New Product"))

    def test_read_other_profile_authorized(self):
        self.other_seller = Seller.objects.get(pk=2)
        self.login_user(self.user)
        response = self.client.get(reverse(
            'seller_profile', kwargs={'store_name': self.other_seller.store_name}),
            follow=True
        )
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You don&#x27;t have permission to access other store profile.")
        )

    def test_seller_profile_search(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            {"search": self.active_product.product_name},
        )
        self.assertContains(response, self.active_product.product_name)
        for other in Product.objects.filter(
            seller=self.seller
        ).exclude(pk=self.active_product.pk):
            self.assertNotContains(response, other.product_name)

    def test_seller_profile_filter_active(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            {"status": "active"},
        )
        self.assertContains(response, self.active_product.product_name)
        self.assertNotContains(response, self.unavailable_product.product_name)
        self.assertNotContains(response, self.out_of_stock_product.product_name)

    def test_seller_profile_filter_inactive(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            {"status": "inactive"},
        )
        self.assertNotContains(response, self.active_product.product_name)
        self.assertContains(response, self.unavailable_product.product_name)
        self.assertNotContains(response, self.out_of_stock_product.product_name)

    def test_seller_profile_filter_out_of_stock(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            {"status": "out"},
        )
        self.assertNotContains(response, self.active_product.product_name)
        self.assertNotContains(response, self.unavailable_product.product_name)
        self.assertContains(response, self.out_of_stock_product.product_name)

    def test_seller_profile_sort_name(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            {"sort": "product_name"},
        )
        self.assertEqual(response.status_code, 200)

    def test_seller_profile_ajax_returns_json(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/json",
        )
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("has_next", data)
        self.assertIn("next_page", data)

    def test_seller_profile_ajax_uses_seller_grid(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse(
                "seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        html = response.json()["html"]
        self.assertIn(_("Edit Product"), html)
        self.assertIn("product-active-toggle", html)

    def test_load_more_pages_do_not_overlap(self):
        self.login_user(self.user)
        self.create_extra_products(SellerProfileView.paginate_by + 5)
        url = reverse(
            "seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        page_1_ids = {
            product.pk
            for product in response.context["products"]
        }
        response = self.client.get(url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        page_2_ids = {
            product.pk
            for product in response.context["products"]
        }
        self.assertTrue(
            page_1_ids.isdisjoint(page_2_ids)
        )

    def test_load_more_button_visibility(self):
        self.login_user(self.user)
        self.create_extra_products(SellerProfileView.paginate_by + 5)
        url = reverse(
            "seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Load More"))
        last_page = response.context["page_obj"].paginator.num_pages
        response = self.client.get(url, {"page": last_page})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, _("Load More"))

    def test_seller_profile_ajax_last_page(self):
        self.login_user(self.user)
        self.create_extra_products(SellerProfileView.paginate_by + 5)
        url = reverse(
            "seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        last_page = response.context["page_obj"].paginator.num_pages
        response = self.client.get(
            url,
            {"page": last_page},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("products_html", data)
        self.assertIn("has_next", data)
        self.assertIn("next_page", data)
        self.assertFalse(data["has_next"])
        self.assertIsNone(data["next_page"])

    def test_seller_profile_search_is_applied_on_page_2(self):
        self.login_user(self.user)
        self.create_extra_products(
            SellerProfileView.paginate_by + 5
        )
        url = reverse(
            "seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        search = "Private Profile Product"
        response = self.client.get(
            url,
            {"search": search, "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page_obj"].has_next())
        response = self.client.get(
            url,
            {"search": search, "page": 2},
        )
        self.assertEqual(response.status_code, 200)
        for product in response.context["products"]:
            self.assertIn(
                search.lower(),
                product.product_name.lower(),
            )

    def test_seller_profile_active_filter_is_applied_on_page_2(self):
        self.login_user(self.user)
        self.create_extra_products(
            SellerProfileView.paginate_by + 5
        )
        url = reverse(
            "seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(
            url,
            {"status": "active", "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page_obj"].has_next())
        response = self.client.get(
            url,
            {"status": "active", "page": 2},
        )
        self.assertEqual(response.status_code, 200)
        for product in response.context["products"]:
            self.assertTrue(product.is_active)
            self.assertGreater(product.stock_quantity, 0)

    def test_seller_profile_inactive_filter_is_applied_on_page_2(self):
        self.login_user(self.user)
        products = self.create_extra_products(
            SellerProfileView.paginate_by + 5
        )
        Product.objects.filter(
            pk__in=[product.pk for product in products]
        ).update(is_active=False)
        url = reverse(
            "seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(
            url,
            {"status": "inactive", "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page_obj"].has_next())
        response = self.client.get(
            url,
            {"status": "inactive", "page": 2},
        )
        self.assertEqual(response.status_code, 200)
        for product in response.context["products"]:
            self.assertFalse(product.is_active)

    def test_seller_profile_out_filter_is_applied_on_page_2(self):
        self.login_user(self.user)
        products = self.create_extra_products(
            SellerProfileView.paginate_by + 5
        )
        Product.objects.filter(
            pk__in=[product.pk for product in products]
        ).update(stock_quantity=0)
        url = reverse(
            "seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(
            url,
            {"status": "out", "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page_obj"].has_next())
        response = self.client.get(
            url,
            {"status": "out", "page": 2},
        )
        self.assertEqual(response.status_code, 200)
        for product in response.context["products"]:
            self.assertEqual(product.stock_quantity, 0)


class TestPublicSellerProfileRead(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=3)
        self.seller.is_verified = True
        self.seller.save()
        self.user = User.objects.get(pk=1)  # not self.seller.user
        self.active_product = Product.objects.get(pk=1)
        self.unavailable_product = Product.objects.get(pk=2)
        self.out_of_stock_product = Product.objects.get(pk=3)
        self.other_seller_product = Product.objects.get(pk=4)

    def create_extra_products(self, count):
        products = []
        for i in range(count):
            product = Product.objects.create(
                product_name=f"Public Profile Product {i}",
                product_price=10 + i,
                stock_quantity=5,
                seller=self.seller,
                category=self.active_product.category,
                origin_city=self.active_product.origin_city,
                is_active=True,
                is_deleted=False,
            )
            products.append(product)
        return products

    def test_read_public_profile_unauthorized(self):
        response = self.client.get(reverse(
            'public_seller_profile', kwargs={'store_name': self.seller.store_name}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.seller.store_name)
        self.assertContains(response, self.active_product.product_name)
        self.assertNotContains(response, self.unavailable_product.product_name)
        self.assertNotContains(response, self.out_of_stock_product.product_name)
        self.assertNotContains(response, self.other_seller_product.product_name)
        self.assertContains(response, _("Available Products"))
        self.assertNotContains(response, _("Your Products"))
        self.assertNotContains(response, _("Store Settings"))
        self.assertNotContains(response, _("Add New Product"))

    def test_read_public_profile_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'public_seller_profile', kwargs={'store_name': self.seller.store_name}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.seller.store_name)
        self.assertContains(response, self.active_product.product_name)
        self.assertNotContains(response, self.unavailable_product.product_name)
        self.assertNotContains(response, self.out_of_stock_product.product_name)
        self.assertNotContains(response, self.other_seller_product.product_name)
        self.assertContains(response, _("Available Products"))
        self.assertNotContains(response, _("Your Products"))
        self.assertNotContains(response, _("Store Settings"))
        self.assertNotContains(response, _("Add New Product"))

    def test_deleted_seller_profile_returns_404(self):
        self.login_user(self.user)
        self.seller.is_deleted = True
        self.seller.save()
        response = self.client.get(
            reverse(
                'public_seller_profile', kwargs={'store_name': self.seller.store_name}
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_unverified_seller_profile_returns_404(self):
        self.seller.is_verified = False
        self.seller.save()
        response = self.client.get(
            reverse(
                "public_seller_profile",
                kwargs={"store_name": self.seller.store_name},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_public_seller_profile_search(self):
        response = self.client.get(
            reverse(
                "public_seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            {"search": self.active_product.product_name},
        )
        self.assertContains(response, self.active_product.product_name)
        for other in Product.objects.filter(
            seller=self.seller,
            is_active=True,
            is_deleted=False,
        ).exclude(pk=self.active_product.pk):
            self.assertNotContains(response, other.product_name)

    def test_public_seller_profile_search_is_accent_insensitive(self):
        self.active_product.product_name = "Café Molido"
        self.active_product.save()
        response = self.client.get(
            reverse(
                "public_seller_profile",
                kwargs={"store_name": self.seller.store_name},
            ),
            {"search": "cafe"},
        )
        self.assertContains(response, self.active_product.product_name)

    def test_load_more_pages_do_not_overlap(self):
        self.create_extra_products(PublicSellerProfileView.paginate_by + 5)
        url = reverse(
            "public_seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        page_1_ids = {
            product.pk
            for product in response.context["products"]
        }
        response = self.client.get(url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        page_2_ids = {
            product.pk
            for product in response.context["products"]
        }
        self.assertTrue(
            page_1_ids.isdisjoint(page_2_ids)
        )

    def test_load_more_button_visibility(self):
        self.create_extra_products(PublicSellerProfileView.paginate_by + 5)
        url = reverse(
            "public_seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Load More"))
        last_page = response.context["page_obj"].paginator.num_pages
        response = self.client.get(url, {"page": last_page})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, _("Load More"))

    def test_public_seller_profile_ajax_last_page(self):
        self.create_extra_products(PublicSellerProfileView.paginate_by + 5)
        url = reverse(
            "public_seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        last_page = response.context["page_obj"].paginator.num_pages
        response = self.client.get(
            url,
            {"page": last_page},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("products_html", data)
        self.assertIn("has_next", data)
        self.assertIn("next_page", data)
        self.assertFalse(data["has_next"])
        self.assertIsNone(data["next_page"])

    def test_public_seller_profile_search_is_applied_on_page_2(self):
        self.create_extra_products(
            PublicSellerProfileView.paginate_by + 5
        )
        url = reverse(
            "public_seller_profile",
            kwargs={"store_name": self.seller.store_name},
        )
        search = "Public Profile Product"
        response = self.client.get(
            url,
            {"search": search, "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page_obj"].has_next())
        response = self.client.get(
            url,
            {"search": search, "page": 2},
        )
        self.assertEqual(response.status_code, 200)
        for product in response.context["products"]:
            self.assertIn(
                search.lower(),
                product.product_name.lower(),
            )


class TestSellerListRead(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=1)
        self.seller.is_verified = True
        self.seller.save()
        self.user = User.objects.get(pk=1)

    def create_extra_sellers(self, count):
        sellers = []
        for i in range(count):
            seller = Seller.objects.create(
                user=User.objects.create_user(
                    username=f"pagination_seller_{i}",
                    email=f"email_{i}@test.com",
                    password="correct_password"
                ),
                store_name=f"Pagination Store {i}",
                website=f"https://test-store-{i}.com",
                is_verified=True,
                is_deleted=False,
            )
            sellers.append(seller)
        return sellers

    def test_read_seller_list_unauthorized(self):
        response = self.client.get(reverse('seller_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.seller.store_name)

    def test_read_seller_list_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse('seller_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.seller.store_name)

    def test_read_seller_list_authorized_with_deleted_seller(self):
        self.seller.is_deleted = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.get(reverse('seller_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.seller.store_name)

    def test_unverified_seller_not_visible_in_seller_list(self):
        self.seller.is_verified = False
        self.seller.save()
        response = self.client.get(reverse("seller_list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.seller.store_name)

    def test_read_seller_list_empty(self):
        Product.objects.all().delete()
        Seller.objects.all().delete()
        response = self.client.get(reverse('seller_list'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("No sellers found."))

    def test_seller_list_search(self):
        response = self.client.get(
            reverse("seller_list"),
            {"search": self.seller.store_name},
        )
        self.assertContains(response, self.seller.store_name)
        for other in Seller.objects.filter(is_deleted=False).exclude(
            pk=self.seller.pk
        ):
            self.assertNotContains(response, other.store_name)

    def test_seller_list_search_is_accent_insensitive(self):
        self.seller.store_name = "José Store"
        self.seller.save()
        response = self.client.get(
            reverse("seller_list"),
            {"search": "jose"},
        )
        self.assertContains(response, self.seller.store_name)

    def test_load_more_pages_do_not_overlap(self):
        self.create_extra_sellers(SellerListView.paginate_by + 5)
        url = reverse("seller_list")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        page_1_ids = {
            seller.pk
            for seller in response.context["sellers"]
        }
        response = self.client.get(url, {"page": 2})
        self.assertEqual(response.status_code, 200)
        page_2_ids = {
            seller.pk
            for seller in response.context["sellers"]
        }
        self.assertTrue(
            page_1_ids.isdisjoint(page_2_ids)
        )

    def test_load_more_button_visibility(self):
        self.create_extra_sellers(SellerListView.paginate_by + 5)
        url = reverse("seller_list")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Load More"))
        last_page = response.context["paginator"].num_pages
        response = self.client.get(url, {"page": last_page})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, _("Load More"))

    def test_seller_list_ajax_last_page(self):
        self.create_extra_sellers(SellerListView.paginate_by + 5)
        url = reverse("seller_list")
        response = self.client.get(url, {"page": 1})
        self.assertEqual(response.status_code, 200)
        last_page = response.context["paginator"].num_pages
        response = self.client.get(
            url,
            {"page": last_page},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
        self.assertIn("sellers_html", data)
        self.assertIn("has_next", data)
        self.assertIn("next_page", data)
        self.assertFalse(data["has_next"])
        self.assertIsNone(data["next_page"])

    def test_seller_list_search_pagination(self):
        self.create_extra_sellers(SellerListView.paginate_by + 5)
        url = reverse("seller_list")
        search = "Pagination"
        response = self.client.get(
            url,
            {"search": search, "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page_obj"].has_next())
        page_1_sellers = list(response.context["sellers"])
        response = self.client.get(
            url,
            {"search": search, "page": 2},
        )
        self.assertEqual(response.status_code, 200)
        page_2_sellers = list(response.context["sellers"])
        page_1_ids = {
            seller.pk
            for seller in page_1_sellers
        }
        page_2_ids = {
            seller.pk
            for seller in page_2_sellers
        }
        self.assertTrue(
            page_1_ids.isdisjoint(page_2_ids)
        )
        for seller in page_1_sellers + page_2_sellers:
            self.assertIn(
                search.lower(),
                seller.store_name.lower(),
            )


class TestBecomeSellerPage(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=1)
        self.user = User.objects.get(pk=self.seller.user.pk)
        self.user_without_store = User.objects.get(pk=1)
        with open(join(FIXTURE_PATH, "sellers_test_data.json")) as f:
            self.sellers_data = json.load(f)
        self.complete_seller_data = self.sellers_data.get("create_complete")

    def test_become_seller_anonymous(self):
        response = self.client.get(reverse('become_seller'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, _("The first step is creating your free account.")
        )
        self.assertContains(response, _("Log in or Register"))
        self.assertNotContains(response, _("Let's create your store."))
        self.assertContains(
            response, reverse("login") + f"?next={reverse('become_seller')}"
        )

    def test_login_next_redirect_to_become_seller(self):
        response = self.client.post(
            reverse("login") + "?next=" + reverse("become_seller"),
            {
                "username": self.user_without_store.username,
                "password": "correct_password",
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("become_seller"))

    def test_become_seller_logged_in(self):
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        response = self.client.get(reverse('become_seller'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Let's create your store."))
        self.assertContains(response, _("Create my store"))
        self.assertNotContains(response, _("Log in or Register"))
        self.assertContains(response, reverse("seller_create"))

    def test_become_seller_existing_seller(self):
        self.login_user(self.user)
        response = self.client.get(reverse('become_seller'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Go to my store"))
        self.assertNotContains(response, _("Create my store"))

    def test_become_seller_deleted_seller(self):
        self.login_user(self.user)
        self.seller.is_deleted = True
        self.seller.save()
        response = self.client.get(reverse('become_seller'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _("Please create a new user account if you wish to open another store.")
        )
        self.assertNotContains(response, _("Create my store"))

    def test_become_seller_unverified_user(self):
        self.login_user(self.user_without_store)
        response = self.client.get(
            reverse("become_seller")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _("Verify your email first"),
        )
        self.assertContains(
            response,
            _("Resend verification email"),
        )
        self.assertNotContains(
            response,
            _("Create my store"),
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestSellerCreate(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=1)
        self.user = User.objects.get(pk=self.seller.user.pk)
        self.user_without_store = User.objects.get(pk=1)
        with open(join(FIXTURE_PATH, "sellers_test_data.json")) as f:
            self.sellers_data = json.load(f)
        self.complete_seller_data = self.sellers_data.get("create_complete")
        self.missing_field_seller_data = self.sellers_data.get(
            "create_missing_field"
        )
        self.duplicate_store_name_data = self.sellers_data.get(
            "create_duplicate_store_name"
        )
        self.duplicate_website_data = self.sellers_data.get("create_duplicate_website")
        with open(os.path.join(IMAGE_PATH, "test_img_to_crop.jpg"), 'rb') as img_file:
            self.success_image = SimpleUploadedFile(
                name='test_image_to_crop.jpg',
                content=img_file.read(),
                content_type='image/jpeg'
            )
        with open(os.path.join(IMAGE_PATH, "test_img_new.jpg"), 'rb') as img_file:
            self.new_image = SimpleUploadedFile(
                name='test_image_new.jpg',
                content=img_file.read(),
                content_type='image/jpeg'
            )

    def test_create_seller_success(self):
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.complete_seller_data, follow=True
        )
        new_seller = Seller.objects.get(store_name='complete_seller')
        self.assertIsNotNone(new_seller)
        self.assertTrue(Seller.objects.filter(store_name="complete_seller").exists())
        self.assertFalse(new_seller.is_verified)
        self.assertEqual(new_seller.user, self.user_without_store)
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _("Store is registered and awaiting verification"),
            {'store_name': self.user_without_store.seller.store_name}
        )

    def test_create_seller_with_profile_picture(self):
        data = self.complete_seller_data.copy()
        data['image'] = self.success_image
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'),
            data,
            format='multipart',
            follow=True
        )
        seller = Seller.objects.get(store_name='complete_seller')
        self.assertIsNotNone(seller)
        self.assertTrue(Seller.objects.filter(store_name='complete_seller').exists())
        seller.refresh_from_db()
        img = Image.open(seller.image.path)
        self.assertEqual(img.size, (240, 240))
        self.assertIsNotNone(seller.image)
        self.assertEqual(seller.image.name, f'sellers/{seller.store_name}.jpg')
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _("Store is registered and awaiting verification"),
            {'store_name': self.user_without_store.seller.store_name}
        )

    def test_replace_or_delete_seller_image_deletes_old_file(self):
        data = self.complete_seller_data.copy()
        data['image'] = self.success_image
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        self.client.post(
            reverse('seller_create'),
            data,
            format='multipart',
            follow=True
        )
        seller = Seller.objects.get(store_name='complete_seller')
        old_image_path = seller.image.path
        self.assertTrue(os.path.exists(old_image_path))
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': seller.store_name}),
            data={
                'image': self.new_image,
                'store_name': seller.store_name,
                'website': seller.website,
                'description': seller.description,
                'password_confirm': 'correct_password'
            },
            format='multipart',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        seller.refresh_from_db()
        new_image_path = seller.image.path
        self.assertNotEqual(new_image_path, old_image_path)
        self.assertTrue(os.path.exists(new_image_path))
        self.assertFalse(os.path.exists(old_image_path))
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': seller.store_name}),
            data={
                'store_name': seller.store_name,
                'website': seller.website,
                'description': seller.description,
                'image-clear': 'on',
                'password_confirm': 'correct_password'
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        seller.refresh_from_db()
        self.assertFalse(os.path.exists(new_image_path))

    def test_create_seller_unauthorized(self):
        response = self.client.post(
            reverse('seller_create'), self.complete_seller_data, follow=True
        )
        self.assertRedirectWithMessage(response)

    def test_create_seller_missing_field(self):
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.missing_field_seller_data
        )
        form = response.context['form']
        self.assertFormError(form, 'website', _('This field is required.'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Seller.objects.filter(store_name="missing_field_seller").exists()
        )

    def test_create_duplicate_store_name(self):
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.duplicate_store_name_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'store_name', _('A store with that name already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_website(self):
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('seller_create'), self.duplicate_website_data
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'website',
            _('A store with that website or social media already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_create_duplicate_user_seller(self):
        self.user.email_verified = True
        self.user.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_create'), self.complete_seller_data, follow=True
        )
        self.assertFalse(Seller.objects.filter(store_name="complete_seller").exists())
        self.assertEqual(self.seller.user, self.user)
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _(
                "You already have a store associated with your account. "
                    "Each user can register only one store. If your store has been "
                    "deleted, it cannot be recreated through the website. To operate "
                    "another store, please use a different account or register "
                    "a new one."
            ),
            {'store_name': self.user.seller.store_name}
        )

    def test_unverified_user_cannot_create_seller(self):
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse("seller_create"),
            self.complete_seller_data,
            follow=True,
        )
        self.assertFalse(
            Seller.objects.filter(
                store_name="complete_seller"
            ).exists()
        )
        self.assertRedirectWithMessage(
            response,
            "become_seller",
            _("Please verify your email address before creating a store."),
        )

    def test_verified_user_can_create_seller(self):
        self.user_without_store.email_verified = True
        self.user_without_store.save()
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse("seller_create"),
            self.complete_seller_data,
            follow=True,
        )
        seller = Seller.objects.get(
            store_name="complete_seller"
        )
        self.assertEqual(
            seller.user,
            self.user_without_store,
        )
        self.assertFalse(seller.is_verified)
        self.assertRedirectWithMessage(
            response,
            "seller_profile",
            _("Store is registered and awaiting verification"),
            {"store_name": seller.store_name},
        )


class TestSellerUpdate(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=1)
        self.user = User.objects.get(pk=self.seller.user.pk)
        with open(join(FIXTURE_PATH, "sellers_test_data.json")) as f:
            self.sellers_data = json.load(f)
        self.complete_seller_data = self.sellers_data.get("update_complete")
        self.missing_field_seller_data = self.sellers_data.get(
            "update_missing_field"
        )
        self.duplicate_store_name_data = self.sellers_data.get(
            "update_duplicate_store_name"
        )
        self.attempt_to_change_website_data = self.sellers_data.get(
            "update_attempt_to_change_website"
        )
        self.change_user_attempt_data = self.sellers_data.get("change_user_attempt")

    def test_update_seller_success(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.complete_seller_data, follow=True
        )
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.store_name, 'new_store_name')
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _("Store is updated successfully"),
            {'store_name': self.seller.store_name}
        )

    def test_impossible_to_change_user(self):
        self.login_user(self.user)
        self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.change_user_attempt_data
        )
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.user, self.user)

    def test_update_seller_missing_field(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.missing_field_seller_data
        )
        form = response.context['form']
        self.assertFormError(form, 'store_name', _('This field is required.'))
        self.assertEqual(response.status_code, 200)

    def test_update_duplicate_store_name(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.duplicate_store_name_data
        )
        form = response.context['form']
        self.assertFormError(
            form, 'store_name', _('A store with that name already exists.')
        )
        self.assertEqual(response.status_code, 200)

    def test_update_attempt_to_change_website(self):
        self.login_user(self.user)
        self.client.post(
            reverse('seller_update', kwargs={'store_name': self.seller.store_name}),
            self.attempt_to_change_website_data,
            follow=True
        )
        self.seller.refresh_from_db()
        self.assertNotEqual(self.seller.website, 'https://changewebsite.test')

    def test_update_other_seller(self):
        self.other_seller = Seller.objects.get(pk=2)
        self.login_user(self.user)
        response = self.client.get(
            reverse('seller_update',
            kwargs={'store_name': self.other_seller.store_name}),
            follow=True
        )
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to access other store profile.")
        )

    def test_update_seller_unauthorized(self):
        response = self.client.get(
            reverse(
                'seller_update',
                kwargs={'store_name': self.seller.store_name}
            ), follow=True
        )
        self.assertRedirectWithMessage(response)

    def test_seller_city(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        self.seller.refresh_from_db()
        self.assertIsNone(self.seller.city)
        data = self.complete_seller_data.copy()
        data['city'] = 2
        data['delivery_cities'] = [1, 2]
        response = self.client.post(
            reverse('seller_update', kwargs={
                'store_name': self.seller.store_name
            }),
            data,
            follow=True
        )
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.city.pk, 2)
        self.assertEqual(
            list(self.seller.delivery_cities.values_list('pk', flat=True)), [1, 2]
        )
        response = self.client.get(reverse('product_create'))
        form = response.context['form']
        self.assertEqual(form.initial['origin_city'], self.seller.city)
        self.assertCountEqual(
            form.initial['delivery_cities'],
            list(self.seller.delivery_cities.values_list('pk', flat=True))
        )


class TestSellerDelete(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=1)
        self.seller_with_product = Seller.objects.get(pk=3)
        self.user = User.objects.get(pk=self.seller.user.pk)
        self.user_with_seller_with_product = User.objects.get(
            pk=self.seller_with_product.user.pk
        )

    def test_delete_seller_success(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.is_deleted)
        self.assertTrue(User.objects.filter(pk=3).exists())
        self.assertRedirectWithMessage(
            response, 'index', _("Store deleted successfully")
        )

    def test_delete_seller_unauthorized(self):
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_deleted)
        self.assertRedirectWithMessage(response)

    def test_delete_seller_wrong_password(self):
        self.login_user(self.user)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller.store_name}
            ), {'password_confirm': 'wrong_password'}, follow=True
        )
        self.seller.refresh_from_db()
        self.assertFalse(self.seller.is_deleted)
        form = response.context['form']
        self.assertFormError(
            form, 'password_confirm', _("Incorrect password.")
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_other_seller(self):
        self.login_user(self.user)
        self.other_seller = Seller.objects.get(pk=2)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.other_seller.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.other_seller.refresh_from_db()
        self.assertFalse(self.other_seller.is_deleted)
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to access other store profile.")
        )

    def test_delete_seller_with_product(self):
        self.login_user(self.user_with_seller_with_product)
        response = self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller_with_product.store_name}
            ), {'password_confirm': 'correct_password'}, follow=True
        )
        self.seller_with_product.refresh_from_db()
        self.assertTrue(self.seller_with_product.is_deleted)
        self.assertFalse(
            self.seller_with_product.seller_products.filter(is_deleted=False).exists()
        )
        self.assertFalse(
            self.seller_with_product.seller_products.filter(is_active=True).exists()
        )
        self.assertRedirectWithMessage(
            response, 'index', _("Store deleted successfully")
        )

    def test_delete_already_deleted_seller(self):
        self.login_user(self.user)
        self.seller.is_deleted = True
        self.seller.save()
        response = self.client.post(
            reverse('seller_delete', kwargs={'store_name': self.seller.store_name}),
            {'password_confirm': 'correct_password'},
            follow=True
        )
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.is_deleted)
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don't have permission to access other store profile.")
        )

    def test_products_invisible_after_seller_deletion(self):
        self.login_user(self.user_with_seller_with_product)
        self.client.post(
            reverse(
                'seller_delete',
                kwargs={'store_name': self.seller_with_product.store_name}
            ),
            {'password_confirm': 'correct_password'},
            follow=True
        )
        response = self.client.get(
            reverse(
                'product_card',
                kwargs={'slug': self.seller_with_product.seller_products.first().slug}
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_create_new_seller_after_deletion(self):
        self.user.email_verified = True
        self.user.save()
        self.login_user(self.user)
        self.seller.is_deleted = True
        self.seller.save()
        response = self.client.get(reverse('seller_create'), follow=True)
        self.assertRedirectWithMessage(
            response, 'index',
                _(
                    "You already have a store associated with your account. "
                    "Each user can register only one store. If your store has been "
                    "deleted, it cannot be recreated through the website. To operate "
                    "another store, please use a different account or register "
                    "a new one."
                )
        )

    def test_seller_tools_not_visible_after_deletion(self):
        self.login_user(self.user)
        self.seller.is_deleted = True
        self.seller.save()
        response = self.client.get(reverse('index'))
        html = response.content.decode()
        self.assertNotIn(_("Seller tools"), html)
        self.assertNotIn(_("Manage my products"), html)
        self.assertNotIn(_("Add new product"), html)


class TestUserModeSwitch(BaseTestCase):

    def setUp(self):
        self.seller = Seller.objects.get(pk=3)
        self.user_seller = User.objects.get(pk=self.seller.user.pk)
        self.normal_user = User.objects.get(pk=1)

    def test_default_mode_for_anonymous_user(self):
        response = self.client.get(reverse('index'))
        html = response.content.decode()
        assert _('Switch to Seller Mode') not in html
        assert _('Switch to User Mode') not in html
        assert response.context['mode'] == 'user'

    def test_default_mode_for_normal_user(self):
        self.login_user(self.normal_user)
        response = self.client.get(reverse('index'))
        html = response.content.decode()
        assert _('Switch to Seller Mode') not in html
        assert _('Switch to User Mode') not in html
        assert response.context['mode'] == 'user'

    def test_default_mode_for_seller(self):
        self.login_user(self.user_seller)
        response = self.client.get(reverse('index'))
        html = response.content.decode()
        assert _('Switch to Seller Mode') in html
        assert _('Switch to User Mode') not in html
        assert response.context['mode'] == 'user'

    def test_switch_to_seller_mode(self):
        self.login_user(self.user_seller)
        response = self.client.post(
            reverse('switch_mode'), {'mode': 'seller'}, follow=True
        )
        html = response.content.decode()
        assert _('Switch to Seller Mode') not in html
        assert _('Switch to User Mode') in html
        assert self.client.session['mode'] == 'seller'
        assert response.context['mode'] == 'seller'

    def test_switch_back_to_user_mode(self):
        self.login_user(self.user_seller)
        self.client.post(
            reverse('switch_mode'), {'mode': 'seller'}, follow=True
        )
        response = self.client.post(
            reverse('switch_mode'), {'mode': 'user'}, follow=True
        )
        html = response.content.decode()
        assert _('Switch to Seller Mode') in html
        assert _('Switch to User Mode') not in html
        assert self.client.session['mode'] == 'user'
        assert response.context['mode'] == 'user'

    def test_non_seller_cannot_switch_to_seller_mode(self):
        self.login_user(self.normal_user)
        response = self.client.post(
            reverse('switch_mode'), {'mode': 'seller'}, follow=True
        )
        html = response.content.decode()
        assert _('Switch to Seller Mode') not in html
        assert _('Switch to User Mode') not in html
        assert self.client.session['mode'] == 'user'
        assert response.context['mode'] == 'user'

    def test_mode_resets_on_logout(self):
        self.login_user(self.user_seller)
        self.client.post(
            reverse('switch_mode'), {'mode': 'seller'}, follow=True
        )
        self.client.logout()
        response = self.client.get(reverse('index'))
        html = response.content.decode()
        assert _('Switch to Seller Mode') not in html
        assert _('Switch to User Mode') not in html
        assert self.client.session['mode'] == 'user'
        assert response.context['mode'] == 'user'
