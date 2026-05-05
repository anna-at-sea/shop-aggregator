import hashlib

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


def validate_image(image):
    max_size_mb = 15
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(_(f"Image size should not exceed {max_size_mb} MB."))


def image_upload_path(instance, filename):
    extension = filename.split('.')[-1]
    model_name = instance._meta.verbose_name.lower()
    folder = f"{model_name}s"
    if hasattr(instance, "slug") and instance.slug:
        name = instance.slug
    elif hasattr(instance, "username") and instance.username:
        name = instance.username
    elif hasattr(instance, "store_name") and instance.store_name:
        name = instance.store_name
    else:
        name = f"{model_name}-{instance.pk or 'unassigned'}"
    print(f"{folder}/{name}.{extension.lower()}")
    return f"{folder}/{name}.{extension.lower()}"


def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
