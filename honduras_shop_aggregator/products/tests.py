import json
import os
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _
from PIL import Image

from honduras_shop_aggregator.products.models import Product
from honduras_shop_aggregator.sellers.models import Seller
from honduras_shop_aggregator.users.models import User
from honduras_shop_aggregator.utils import BaseTestCase, get_file_hash

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
        with open(os.path.join(FIXTURE_PATH, "products_test_data.json")) as f:
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
        with open(
            os.path.join(IMAGE_PATH, "test_img_bigger_than_2_mb.jpg"), 'rb'
        ) as img_file:
            self.big_image = SimpleUploadedFile(
                name='test_img_bigger_than_2_mb.jpg',
                content=img_file.read(),
                content_type='image/jpeg'
            )
        with open(
            os.path.join(IMAGE_PATH, "test_img_wrong_format.txt"), 'rb'
        ) as txt_file:
            self.wrong_format = SimpleUploadedFile(
                name='test_img_wrong_format.txt',
                content=txt_file.read(),
                content_type='text/plain'
            )
        self.product = Product.objects.all().first()
        self.seller = self.product.seller
        self.user = self.seller.user
        placeholder_src = os.path.join(
            settings.BASE_DIR, 'media', 'products', 'placeholder.png'
        )
        placeholder_dest = os.path.join(TEMP_MEDIA_ROOT, 'products', 'placeholder.png')
        os.makedirs(os.path.dirname(placeholder_dest), exist_ok=True)
        shutil.copyfile(placeholder_src, placeholder_dest)

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
        placeholder_path = os.path.join(TEMP_MEDIA_ROOT, 'products', 'placeholder.png')
        self.assertTrue(os.path.exists(placeholder_path))

    def test_image_upload_too_big(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug}),
            data={'image': self.big_image}
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'image',
            _("Image size should not exceed 2 MB.")
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, 'products/placeholder.png')

    def test_image_upload_wrong_format(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug}),
            data={'image': self.wrong_format}
        )
        form = response.context['form']
        self.assertFormError(
            form,
            'image',
            _(
                "Upload a valid image. "
                "The file you uploaded was either not an image or a corrupted image."
            )
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, 'products/placeholder.png')

    def test_placeholder_is_used_by_default(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug})
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, 'products/placeholder.png')

    def test_old_image_replaced_on_new_upload(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug}),
            data={'image': self.success_image},
            follow=True
        )
        self.product.refresh_from_db()
        old_image_path = self.product.image.path
        self.assertTrue(os.path.exists(old_image_path))
        old_hash = get_file_hash(old_image_path)
        self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug}),
            data={'image': self.new_image},
            follow=True
        )
        self.product.refresh_from_db()
        new_image_path = self.product.image.path
        self.assertTrue(
            self.product.image.name.startswith(f'products/{self.product.slug}'),
            msg=_(f"Image name should start with 'products/{self.product.slug}', "
                f"got '{self.product.image.name}'")
        )
        self.assertTrue(os.path.exists(new_image_path))
        new_hash = get_file_hash(new_image_path)
        self.assertNotEqual(
            old_hash, new_hash, _("Image content should change after new upload")
        )

    def test_image_upload_by_non_verified_seller(self):
        self.seller.is_verified = False
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug}),
            data={'image': self.success_image},
            follow=True
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, 'products/placeholder.png')
        self.assertRedirectWithMessage(
            response,
            'index',
            _("Only verified sellers can add and edit products.")
        )

    def test_image_upload_by_other_seller(self):
        other_user = User.objects.get(pk=2)
        other_seller = other_user.seller
        other_seller.is_verified = True
        other_seller.save()
        self.login_user(other_user)
        response = self.client.post(
            reverse('product_update_image', kwargs={'slug': self.product.slug}),
            data={'image': self.success_image},
            follow=True
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, 'products/placeholder.png')
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You don&#x27;t have permission to access this product.")
        )


class TestProductUpdate(BaseTestCase):

    def setUp(self):
        self.product = Product.objects.all().first()
        self.seller = self.product.seller
        self.user = self.seller.user
        with open(os.path.join(FIXTURE_PATH, "products_test_data.json")) as f:
            self.products_data = json.load(f)
        self.complete_product_data = self.products_data.get("update_complete")
        self.missing_field_product_data = self.products_data.get(
            "update_missing_field"
        )
        self.duplicate_name_data = self.products_data.get(
            "update_duplicate_name"
        )
        self.duplicate_link_data = self.products_data.get("update_duplicate_link")
        self.change_seller_attempt_data = self.products_data.get(
            "change_seller_attempt"
        )
        self.zero_price_product_data = self.products_data.get(
            "update_zero_price"
        )
        self.invalid_product_link_data = self.products_data.get(
            "update_invalid_link"
        )
        self.link_in_name_data = self.products_data.get(
            "update_link_in_name"
        )
    def test_update_product_success(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.complete_product_data,
            follow=True
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_name, 'new_product_name')
        self.assertEqual(self.product.slug, 'testproduct')
        self.assertEqual(
            self.product.product_link, 'https://product-store.test/new_product_name'
        )
        self.assertEqual(self.product.product_price, 20)
        self.assertEqual(self.product.description, 'test product update description')
        self.assertNotEqual(self.product.slug, slugify(self.product.product_name))
        self.assertRedirectWithMessage(
            response,
            'product_card',
            _("Product information is updated successfully"),
            {'slug': self.product.slug}
        )

    def test_update_product_unauthorized(self):
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.complete_product_data,
            follow=True
        )
        self.assertNotEqual(self.product.product_name, 'new_product_name')
        self.assertRedirectWithMessage(response)

    def test_update_product_by_other_user(self):
        other_user = User.objects.get(pk=2)
        other_user.seller.is_verified = True
        other_user.seller.save()
        self.login_user(other_user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.complete_product_data,
            follow=True
        )
        self.assertNotEqual(self.product.product_name, 'new_product_name')
        self.assertRedirectWithMessage(
            response,
            'index',
            _("You don&#x27;t have permission to access this product.")
        )

    def test_update_product_by_non_verified_seller(self):
        self.seller.is_verified = False
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.complete_product_data,
            follow=True
        )
        self.assertNotEqual(self.product.product_name, 'new_product_name')
        self.assertRedirectWithMessage(
            response,
            'index',
            _("Only verified sellers can add and edit products.")
        )

    def test_update_product_with_price_zero(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.zero_price_product_data,
            follow=True
        )
        form = response.context['form']
        self.assertFormError(form, 'product_price', _('Price must be greater than 0.'))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.product.product_name, 'new_product_name')

    def test_update_product_invalid_product_link(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.invalid_product_link_data,
            follow=True
        )
        form = response.context['form']
        self.assertFormError(form, 'product_link', _('Enter a valid URL.'))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.product.product_name, 'new_product_name')

    def test_update_product_link_in_name(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.link_in_name_data,
            follow=True
        )
        form = response.context['form']
        self.assertFormError(
            form, 'product_name', _('Product name cannot contain links.')
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.product.product_name, 'new_product_name')

    def test_update_duplicate_product_link(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.duplicate_link_data,
            follow=True
        )
        form = response.context['form']
        self.assertFormError(
            form, 'product_link', _('This product is already listed.')
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(
            self.product.product_link, "https://product-store.test/double_link"
        )

    def test_update_duplicate_product_name(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.duplicate_name_data,
            follow=True
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_name, 'unavailable_product')
        self.assertEqual(self.product.slug, 'testproduct')

    def test_update_product_missing_name(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.missing_field_product_data,
            follow=True
        )
        form = response.context['form']
        self.assertFormError(
            form, 'product_name', _('This field is required.')
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.product.product_name, '')

    def test_impossible_to_change_seller(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        self.client.post(
            reverse('product_update', kwargs={'slug': self.product.slug}),
            self.change_seller_attempt_data,
            follow=True
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.seller, self.seller)
        self.assertNotEqual(
            self.change_seller_attempt_data['seller'],
            self.seller.pk
        )


class TestProductDelete(BaseTestCase):

    def setUp(self):
        self.product = Product.objects.all().first()
        self.seller = self.product.seller
        self.user = self.seller.user

    def test_delete_product_success(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_delete', kwargs={'slug': self.product.slug}),
            {'password_confirm': 'correct_password'},
            follow=True
        )
        self.assertFalse(Product.objects.filter(pk=1).exists())
        self.assertRedirectWithMessage(
            response,
            'seller_profile',
            _("Product deleted successfully"),
            {'store_name': self.seller.store_name}
        )

    def test_delete_product_unauthorized(self):
        response = self.client.post(
            reverse('product_delete', kwargs={'slug': self.product.slug}),
            {'password_confirm': 'correct_password'},
            follow=True
        )
        self.assertTrue(Product.objects.filter(pk=1).exists())
        self.assertRedirectWithMessage(response)

    def test_delete_product_non_verified_seller(self):
        self.seller.is_verified = False
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_delete', kwargs={'slug': self.product.slug}),
            {'password_confirm': 'correct_password'},
            follow=True
        )
        self.assertTrue(Product.objects.filter(pk=1).exists())
        self.assertRedirectWithMessage(
            response,
            'index',
            _("Only verified sellers can add and edit products.")
        )

    def test_delete_product_wrong_password(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        response = self.client.post(
            reverse('product_delete', kwargs={'slug': self.product.slug}),
            {'password_confirm': 'wrong_password'},
            follow=True
        )
        self.assertTrue(Product.objects.filter(pk=1).exists())
        form = response.context['form']
        self.assertFormError(
            form, 'password_confirm', _("Incorrect password.")
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_other_seller_product(self):
        self.seller.is_verified = True
        self.seller.save()
        self.login_user(self.user)
        self.other_seller_product = Product.objects.get(pk=4)
        response = self.client.post(
            reverse('product_delete', kwargs={'slug': self.other_seller_product.slug}),
            {'password_confirm': 'correct_password'},
            follow=True
        )
        self.assertTrue(Product.objects.filter(pk=4).exists())
        self.assertRedirectWithMessage(
            response, 'index',
            _("You don&#x27;t have permission to access this product.")
        )
