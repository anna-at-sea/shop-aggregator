import hashlib

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from PIL import Image


def validate_image(image):
    max_size_mb = 15
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(_(f"Image size should not exceed {max_size_mb} MB."))


def image_upload_path(instance, filename):
    extension = filename.split('.')[-1]
    model_name = instance._meta.verbose_name.lower()
    folder = f"{model_name}s"
    if hasattr(instance, "product") and instance.product.slug:
        name = instance.product.slug + "-gallery-" + str(instance.order)
    elif hasattr(instance, "slug") and instance.slug:
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


def process_image(image_path, size=(1200, 1200)):
    """
    Keeps the whole image visible.

    The image is resized so that its longest side becomes
    the target size while preserving aspect ratio.

    Remaining space is filled with white.
    """
    try:
        img = Image.open(image_path)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        target = size[0]
        width, height = img.size
        longest_side = max(width, height)
        scale = target / longest_side
        new_width = round(width * scale)
        new_height = round(height * scale)
        img = img.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new(
            "RGB",
            size,
            (255, 255, 255)
        )
        x = (target - new_width) // 2
        y = (target - new_height) // 2
        canvas.paste(img, (x, y))
        canvas.save(
            image_path,
            quality=90,
            optimize=True
        )
    except Exception as e:
        raise ValidationError(
            _("Image processing failed") + f": {e}"
        )