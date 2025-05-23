import json
import shutil
import tempfile
from os.path import join

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _
from PIL import Image

from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.sellers.models import Seller
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase

FIXTURE_PATH = 'honduras_shop_aggregator/fixtures/'
IMAGE_PATH = 'honduras_shop_aggregator/static/images'
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

class TestProductCardRead(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()
        self.product_active = Product.objects.all().first()
        self.product_not_active = Product.objects.get(pk=2)
        self.product_out_of_stock = Product.objects.get(pk=3)

    def test_read_product_card_unauthorized(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_active.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("In stock"))
        self.assertContains(response, _("Login to Save"))

    def test_read_product_card_authorized(self):
        self.login_user(self.user)
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_active.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("In stock"))
        self.assertContains(response, _("Add to Favorites"))

    def test_read_product_card_not_active(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_not_active.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Out of stock"))
        self.assertNotContains(response, _("Add to Favorites"))
        self.assertNotContains(response, _("Login to Save"))

    def test_read_product_card_out_of_stock(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': self.product_out_of_stock.slug}),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Out of stock"))
        self.assertNotContains(response, _("Add to Favorites"))
        self.assertNotContains(response, _("Login to Save"))

    def test_read_product_non_existent(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': 'non-existent-product'}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_read_product_with_malformed_slug(self):
        response = self.client.get(reverse(
            'product_card', kwargs={'slug': '%%%weird---slug%%%'}),
            follow=True
        )
        self.assertEqual(response.status_code, 404)


class TestProductListRead(BaseTestCase):

    def setUp(self):
        self.user = User.objects.all().first()
        self.product_active = Product.objects.all().first()
        self.product_not_active = Product.objects.get(pk=2)
        self.product_out_of_stock = Product.objects.get(pk=3)

    def test_read_product_list_unauthorized(self):
        response = self.client.get(
            reverse('product_list'),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product_active.product_name)
        self.assertNotContains(response, self.product_not_active.product_name)
        self.assertNotContains(response, self.product_out_of_stock.product_name)

    def test_read_product_list_authorized(self):
        self.login_user(self.user)
        response = self.client.get(
            reverse('product_list'),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product_active.product_name)
        self.assertNotContains(response, self.product_not_active.product_name)
        self.assertNotContains(response, self.product_out_of_stock.product_name)

    def test_read_product_list_empty(self):
        Product.objects.all().delete()
        response = self.client.get(reverse('product_list'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("No products found."))


class TestProductCreate(BaseTestCase):

    def setUp(self):
        self.seller_with_products = Seller.objects.get(pk=3)
        self.seller_without_products = Seller.objects.get(pk=2)
        self.user_with_store_with_products = User.objects.get(
            pk=self.seller_with_products.user.pk
        )
        self.user_with_store_without_products = User.objects.get(
            pk=self.seller_without_products.user.pk
        )
        self.user_without_store = User.objects.all().first()
        with open(join(FIXTURE_PATH, "products_test_data.json")) as f:
            self.products_data = json.load(f)
        self.complete_product_data = self.products_data.get("create_complete")
        self.missing_price_product_data = self.products_data.get(
            "create_missing_price"
        )
        self.missing_name_product_data = self.products_data.get(
            "create_missing_name"
        )
        self.zero_price_product_data = self.products_data.get(
            "create_zero_price"
        )
        self.duplicate_product_name_data = self.products_data.get(
            "create_duplicate_product_name"
        )
        self.duplicate_product_link_data = self.products_data.get(
            "create_duplicate_product_link"
        )
        self.duplicate_product_slug_data = self.products_data.get(
            "create_duplicate_slug"
        )
        self.invalid_product_link_data = self.products_data.get(
            "create_invalid_link"
        )
        self.third_website_product_link_data = self.products_data.get(
            "create_third_website_link"
        )
        self.large_price_data = self.products_data.get(
            "create_large_price"
        )
        self.link_in_name_data = self.products_data.get(
            "create_link_in_name"
        )
        self.link_in_description_data = self.products_data.get(
            "create_link_in_description"
        )

    def test_create_product_success(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.complete_product_data,
            follow=True
        )
        new_product = Product.objects.get(slug='testproduct_1')
        self.assertIsNotNone(new_product)
        self.assertTrue(Product.objects.filter(slug="testproduct_1").exists())
        self.assertEqual(new_product.seller, self.seller_with_products)
        self.assertRedirectWithMessage(
            response,
            'product_update_image',
            _("Product is added successfully. Please add image of the product"),
            {'slug': new_product.slug}
        )

    def test_create_product_unauthorized(self):
        response = self.client.post(
            reverse('product_create'), self.complete_product_data, follow=True
        )
        self.assertFalse(Product.objects.filter(slug="testproduct_1").exists())
        self.assertRedirectWithMessage(response)

    def test_create_product_by_user_without_store(self):
        self.login_user(self.user_without_store)
        response = self.client.post(
            reverse('product_create'),
            self.complete_product_data,
            follow=True
        )
        self.assertFalse(Product.objects.filter(slug="testproduct_1").exists())
        self.assertRedirectWithMessage(
            response,
            'index',
            _("Only verified sellers can add and edit products.")
        )

    def test_create_product_by_non_verified_seller(self):
        self.seller_with_products.is_verified = False
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.complete_product_data,
            follow=True
        )
        self.assertFalse(Product.objects.filter(slug="testproduct_1").exists())
        self.assertRedirectWithMessage(
            response,
            'index',
            _("Only verified sellers can add and edit products.")
        )

    def test_create_product_missing_price(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.missing_price_product_data
        )
        form = response.context['form']
        self.assertFormError(form, 'product_price', _('This field is required.'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(slug="testproduct_missing_price").exists())

    def test_create_product_missing_name(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.missing_name_product_data
        )
        form = response.context['form']
        self.assertFormError(form, 'product_name', _('This field is required.'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Product.objects.filter(
                product_link="https://product-store.test/missing_name"
            ).exists()
        )

    def test_create_product_with_price_zero(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.zero_price_product_data
        )
        form = response.context['form']
        self.assertFormError(form, 'product_price', _('Price must be greater than 0.'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(slug="testproduct_1").exists())

    def test_create_duplicate_product_name_creates_unique_slug(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        initial_product_count = Product.objects.count()
        response = self.client.post(
            reverse('product_create'),
            self.duplicate_product_name_data,
            follow=True
        )
        product_1 = Product.objects.latest('pk')
        self.assertEqual(product_1.slug, "testproduct-1")
        self.assertEqual(Product.objects.count(), initial_product_count + 1)
        self.assertRedirectWithMessage(
            response,
            'product_update_image',
            _("Product is added successfully. Please add image of the product"),
            {'slug': product_1.slug}
        )
        response2 = self.client.post(
            reverse('product_create'),
            self.duplicate_product_name_data,
            follow=True
        )
        product_2 = Product.objects.latest('pk')
        self.assertEqual(product_2.slug, "testproduct-2")
        self.assertEqual(Product.objects.count(), initial_product_count + 2)
        self.assertRedirectWithMessage(
            response2,
            'product_update_image',
            _("Product is added successfully. Please add image of the product"),
            {'slug': product_2.slug}
        )
        self.assertEqual(product_1.product_name, product_2.product_name)
        self.assertNotEqual(product_1.slug, product_2.slug)

    def test_create_duplicate_product_link(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.duplicate_product_link_data
        )
        form = response.context['form']
        self.assertFormError(form, 'product_link', _('This product is already listed.'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Product.objects.filter(slug="testproduct_duplicate_link").exists()
        )

    def test_create_duplicate_slug(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        initial_product_count = Product.objects.count()
        response = self.client.post(
            reverse('product_create'),
            self.duplicate_product_slug_data,
            follow=True
        )
        new_product = Product.objects.latest('pk')
        self.assertEqual(new_product.slug, "testproduct-1")
        self.assertEqual(Product.objects.count(), initial_product_count + 1)
        self.assertRedirectWithMessage(
            response,
            'product_update_image',
            _("Product is added successfully. Please add image of the product"),
            {'slug': new_product.slug}
        )

    def test_create_product_invalid_product_link(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.invalid_product_link_data
        )
        form = response.context['form']
        self.assertFormError(form, 'product_link', _('Enter a valid URL.'))
        self.assertFalse(Product.objects.filter(slug="testproduct_invalid_link").exists())

    def test_create_product_third_website_product_link(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.third_website_product_link_data
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'product_link',
            _("Product link must start with the seller's website URL.")
        )
        self.assertFalse(
            Product.objects.filter(slug="testproduct_third_website_link").exists()
        )

    def test_create_product_large_price(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.large_price_data
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'product_price',
            _('Ensure that there are no more than 10 digits in total.')
        )
        self.assertFalse(Product.objects.filter(slug='testproduct_large_price').exists())

    def test_create_product_link_in_name(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.link_in_name_data
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'product_name',
            _("Product name cannot contain links.")
        )
        self.assertFalse(
            Product.objects.filter(pk=10).exists()
        )

    def test_create_product_link_in_description(self):
        self.seller_with_products.is_verified = True
        self.seller_with_products.save()
        self.login_user(self.user_with_store_with_products)
        response = self.client.post(
            reverse('product_create'),
            self.link_in_description_data
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'description',
            _("Description cannot contain links.")
        )
        self.assertFalse(
            Product.objects.filter(slug="testproduct_link_in_description").exists()
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestImageUpload(BaseTestCase):

    def setUp(self):
        with open(join(IMAGE_PATH, "test_img_to_crop.jpg"), 'rb') as img_file:
            self.success_image = SimpleUploadedFile(
                name='test_image_to_crop.jpg',
                content=img_file.read(),
                content_type='image/jpeg'
            )
        with open(join(IMAGE_PATH, "test_img_bigger_than_2_mb.jpg"), 'rb') as img_file:
            self.big_image = SimpleUploadedFile(
                name='test_img_bigger_than_2_mb.jpg',
                content=img_file.read(),
                content_type='image/jpeg'
            )
        with open(join(IMAGE_PATH, "test_img_wrong_format.txt"), 'rb') as txt_file:
            self.wrong_format = SimpleUploadedFile(
                name='test_img_wrong_format.txt',
                content=txt_file.read(),
                content_type='text/plain'
            )
        self.product = Product.objects.all().first()
        self.seller = self.product.seller
        self.user = self.seller.user
        self.other_user = User.objects.all().first()

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_image_upload_success(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug}),
            data={'image': self.success_image},
            follow=True
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, f'products/{self.product.slug}.jpg')
        self.assertRedirectWithMessage(
            response,
            'product_card',
            _("Image updated successfully"),
            {'slug': self.product.slug}
        )
        img_path = self.product.image.path
        with Image.open(img_path) as img:
            width, height = img.size
            self.assertEqual(
                (width, height),
                (500, 500),
                msg="Image should be resized to 500x500"
            )
