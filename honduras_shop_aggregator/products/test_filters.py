from django.urls import reverse
from django.utils.translation import gettext as _

from honduras_shop_aggregator.categories.models import Category
from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.utils import BaseTestCase

FIXTURE_PATH = 'honduras_shop_aggregator/fixtures/'


class TestProductSearch(BaseTestCase):

    def setUp(self):
        self.testproduct = Product.objects.get(product_name='testproduct')
        self.other_seller_product = Product.objects.get(
            product_name='other_seller_product'
        )
        self.unavailable_product = Product.objects.get(
            product_name='unavailable_product'
        )
        self.out_of_stock_product = Product.objects.get(
            product_name='out_of_stock_product'
        )
        self.product_with_matching_description_correct_city_1 = Product.objects.get(
            pk=1
        )
        self.product_with_matching_description_correct_city_2 = Product.objects.get(
            pk=4
        )
        self.product_with_matching_description_wrong_city = Product.objects.get(
            pk=6
        )
        self.other_category_product = Product.objects.get(
            product_name='other category product'
        )
        session = self.client.session
        session['city_pk'] = 1
        session.save()

    def test_global_search_full_name(self):
        response = self.client.get(
            reverse('product_list'),
            {"search": "testproduct"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.testproduct.product_name)

    def test_global_search_part_name(self):
        response = self.client.get(
            reverse('product_list'),
            {"search": "other product"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.other_seller_product.product_name)
        self.assertContains(response, self.other_category_product.product_name)
        self.assertNotContains(response, self.testproduct.product_name)
        response = self.client.get(
            reverse('product_list'),
            {"search": "product"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.other_seller_product.product_name)
        self.assertContains(response, self.testproduct.product_name)
        self.assertNotContains(response, self.unavailable_product.product_name)
        self.assertNotContains(response, self.out_of_stock_product.product_name)
        self.assertNotContains(
            response, self.product_with_matching_description_wrong_city.product_name
        )  # it also contains "product" in name but it is from city 2

    def test_global_search_match_in_description(self):
        response = self.client.get(
            reverse('product_list'),
            {"search": "this is"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.product_with_matching_description_correct_city_1.product_name
        )
        self.assertContains(
            response,
            self.product_with_matching_description_correct_city_2.product_name
        )
        self.assertNotContains(
            response, self.product_with_matching_description_wrong_city.product_name
        )

    def test_case_and_accent_insensitivity(self):
        response = self.client.get(
            reverse('product_list'),
            {"search": "Cátegory"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.other_category_product.product_name
        )

    def test_global_search_empty_queryset(self):
        response = self.client.get(
            reverse('product_list'),
            {"search": "non-existent product"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _('No products found.')
        )

    def test_global_search_ignoring_punctuation(self):
        response = self.client.get(
            reverse('product_list'),
            {"search": "@testproduct!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.testproduct.product_name
        )


class TestProductFilters(BaseTestCase):

    def setUp(self):
        self.product_price_10_cat_1_sel_3 = Product.objects.get(pk=1)
        self.product_price_50_cat_1_sel_2 = Product.objects.get(pk=4)
        self.product_price_555_cat_3_sel_3 = Product.objects.get(pk=5)
        self.unavailable_product = Product.objects.get(
            product_name='unavailable_product'
        )
        self.out_of_stock_product = Product.objects.get(
            product_name='out_of_stock_product'
        )
        session = self.client.session
        session['city_pk'] = 1
        session.save()

    def test_price_from_to_filter(self):
        response = self.client.get(
            reverse('product_list'),
            {"price_min": 20, "price_max": 500}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.unavailable_product.product_name
        )
        self.assertNotContains(
            response,
            self.out_of_stock_product.product_name
        )
        response = self.client.get(
            reverse('product_list'),
            {"price_max": 500}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.unavailable_product.product_name
        )
        self.assertNotContains(
            response,
            self.out_of_stock_product.product_name
        )
        response = self.client.get(
            reverse('product_list'),
            {"price_min": 20}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.unavailable_product.product_name
        )
        self.assertNotContains(
            response,
            self.out_of_stock_product.product_name
        )
        response = self.client.get(
            reverse('product_list'),
            {"price_min": 1000}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _('No products found.')
        )

    def test_category_filter(self):
        response = self.client.get(
            reverse('product_list'),
            {"category": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )

    def test_seller_filter(self):
        response = self.client.get(
            reverse('product_list'),
            {"seller": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.unavailable_product.product_name
        )
        self.assertNotContains(
            response,
            self.out_of_stock_product.product_name
        )

    def test_combined_filters_and_search(self):
        response = self.client.get(
            reverse('product_list'),
            {"price_max": 100, "seller": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.unavailable_product.product_name
        )
        self.assertNotContains(
            response,
            self.out_of_stock_product.product_name
        )
        response = self.client.get(
            reverse('product_list'),
            {"category": 1, "seller": 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        response = self.client.get(
            reverse('product_list'),
            {"seller": 3, "category": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        response = self.client.get(
            reverse('product_list'),
            {"category": 1, "search": "oth"}
            # there is 'other' in names of 2 products
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        response = self.client.get(
            reverse('product_list'),
            {"category": 1, "seller": 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _('No products found.')
        )

    def test_invalid_filters_passed_to_url(self):
        response = self.client.get(
            reverse('product_list'),
            {"price_max": "abc"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _('No products found.')
        )
        response = self.client.get(
            reverse('product_list'),
            {"seller": 1000}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _('No products found.')
        )


class TestSearchAndFiltersInCategories(BaseTestCase):

    def setUp(self):
        self.category_1 = Category.objects.all().first()
        self.category_3 = Category.objects.get(pk=3)
        self.product_price_10_cat_1_sel_3 = Product.objects.get(pk=1)
        self.product_price_50_cat_1_sel_2 = Product.objects.get(pk=4)
        self.product_price_555_cat_3_sel_3 = Product.objects.get(pk=5)
        session = self.client.session
        session['city_pk'] = 1
        session.save()

    def test_category_filter_not_applied_on_category_page(self):
        url = reverse("category_page", kwargs={"slug": self.category_1.slug})
        response_with_filter = self.client.get(url, {"category": 3})
        response_without_filter = self.client.get(url)
        self.assertEqual(
            list(response_with_filter.context["object_list"]),
            list(response_without_filter.context["object_list"]),
        )
        self.assertNotContains(response_without_filter, _("Category"))

    def test_combines_filters_and_search_in_category(self):
        response = self.client.get(
            reverse("category_page", kwargs={"slug": self.category_1.slug}),
            {"min_price": 50, "seller": 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        response = self.client.get(
            reverse("category_page", kwargs={"slug": self.category_1.slug}),
            {"search": "testproduct", "seller": 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        response = self.client.get(
            reverse("category_page", kwargs={"slug": self.category_3.slug}),
            {"price_max": 560, "seller": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.product_price_50_cat_1_sel_2.product_name
        )
        self.assertNotContains(
            response,
            self.product_price_10_cat_1_sel_3.product_name
        )
        self.assertContains(
            response,
            self.product_price_555_cat_3_sel_3.product_name
        )
        response = self.client.get(
            reverse("category_page", kwargs={"slug": self.category_3.slug}),
            {"price_max": 500, "seller": 3}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            _('No products found.')
        )
