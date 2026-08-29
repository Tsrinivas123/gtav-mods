import os
import mimetypes
from io import BytesIO
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image
import zipfile

# Security configurations
BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.ps1', '.sh', '.php', '.py', '.js'}
ALLOWED_IMAGE_TYPES = {
    'jpg': ['image/jpeg', 'image/pjpeg'],
    'jpeg': ['image/jpeg', 'image/pjpeg'],
    'png': ['image/png'],
    'webp': ['image/webp']
}
ALLOWED_ARCHIVE_MIMES = {
    'application/zip',
    'application/x-zip-compressed',
    'application/x-zip',
    'application/x-compressed',
    'application/octet-stream',
    'application/x-rar-compressed',
    'application/x-rar',
    'application/vnd.rar',
    'application/x-7z-compressed',
}

MAX_FILE_SIZE_MB = 100  # Customizable max size limit

def validate_image_file(uploaded_file):
    """
    Validates image file extension, MIME type, and tests opening with Pillow to verify it is not corrupted or spoofed.
    """
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    
    # Check extension
    if ext not in ALLOWED_IMAGE_TYPES:
        raise ValidationError(f"Invalid image format '.{ext}'. Allowed formats: jpg, jpeg, png, webp.")
    
    # Validate MIME type
    content_type = uploaded_file.content_type
    if content_type not in ALLOWED_IMAGE_TYPES[ext]:
        # Fallback guessed mime type checking
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type not in ALLOWED_IMAGE_TYPES[ext]:
            raise ValidationError(f"MIME type '{content_type}' does not match file extension '.{ext}'.")
            
    # Validate file contents by opening with Pillow
    try:
        # Save current pointer, read and reset
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img.verify()
        uploaded_file.seek(0)
    except Exception:
        raise ValidationError("Corrupt or invalid image file contents.")

def resize_image_if_large(uploaded_file, max_dim=1920):
    """
    Checks dimensions of an image and resizes it to fit within max_dim x max_dim.
    Returns a ContentFile if resized, otherwise returns original.
    """
    uploaded_file.seek(0)
    try:
        img = Image.open(uploaded_file)
        width, height = img.size
        if width > max_dim or height > max_dim:
            # Calculate new size
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            
            # Save to bytes
            buffer = BytesIO()
            # Retain format or use PNG/JPEG
            format = img.format if img.format else 'JPEG'
            img.save(buffer, format=format, quality=85)
            buffer.seek(0)
            
            return ContentFile(buffer.read(), name=uploaded_file.name)
    except Exception:
        pass
    uploaded_file.seek(0)
    return uploaded_file

def validate_archive_file(uploaded_file):
    """
    Validates archive extension, MIME type, size, and verifies the binary file signature to prevent executable spoofing.
    """
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower().replace('.', '')
    
    # Block script files
    if f".{ext}" in BLOCKED_EXTENSIONS:
        raise ValidationError(f"Security Warning: File extension '.{ext}' is blocked.")

    # Check extension
    if ext not in ['zip', 'rar', '7z']:
        raise ValidationError(f"Invalid file format '.{ext}'. Allowed formats: zip, rar, 7z.")
    
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB.")
    
    # Validate MIME type
    content_type = uploaded_file.content_type
    if content_type not in ALLOWED_ARCHIVE_MIMES:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type not in ALLOWED_ARCHIVE_MIMES:
            raise ValidationError(f"MIME type '{content_type}' does not match file extension '.{ext}'.")
            
    # Check Magic Signature Bytes
    uploaded_file.seek(0)
    header = uploaded_file.read(6)
    uploaded_file.seek(0)
    
    # Magic signatures:
    # ZIP: 50 4B 03 04 (PK\x03\x04)
    # RAR: 52 61 72 21 1A 07 (Rar!\x1a\x07)
    # 7Z: 37 7A BC AF 27 1C (7z\xbc\xaf\x27\x1c)
    if ext == 'zip' and not header.startswith(b'PK\x03\x04'):
        raise ValidationError("Invalid archive contents: File signature does not match ZIP format.")
    elif ext == 'rar' and not header.startswith(b'Rar!'):
        raise ValidationError("Invalid archive contents: File signature does not match RAR format.")
    elif ext == '7z' and not header.startswith(b'7z\xbc\xaf'):
        raise ValidationError("Invalid archive contents: File signature does not match 7Z format.")

    # Validate ZIP integrity using zipfile module
    if ext == 'zip':
        try:
            with zipfile.ZipFile(uploaded_file) as zf:
                bad_file = zf.testzip()
                if bad_file is not None:
                    raise ValidationError(f"ZIP archive contains corrupt file: {bad_file}")
        except zipfile.BadZipFile:
            raise ValidationError("Invalid or corrupt ZIP archive.")
        finally:
            uploaded_file.seek(0)

# ─── Service Layer APIs ─────────────────────────────────────────────────────────

def save_main_image(product, uploaded_file):
    """
    Validates, resizes, and saves the main product image, cleaning up any old file on disk.
    """
    validate_image_file(uploaded_file)
    processed_file = resize_image_if_large(uploaded_file)
    
    # Cleanup old file if it exists
    if product.main_image:
        delete_file_from_storage(product.main_image.name)
        
    # Save the new file
    product.main_image.save(uploaded_file.name, processed_file, save=True)
    return product.main_image.url

def delete_main_image(product):
    """
    Removes the main product image from disk and database field.
    """
    if product.main_image:
        delete_file_from_storage(product.main_image.name)
        product.main_image = None
        product.save()

def save_gallery_image(product, uploaded_file):
    """
    Validates, resizes, and appends an image to the product gallery, returning the model instance.
    """
    from marketplace.models import ProductImage
    validate_image_file(uploaded_file)
    processed_file = resize_image_if_large(uploaded_file)
    
    # Calculate next order value
    max_order = 0
    existing = product.screenshots.all()
    if existing.exists():
        max_order = max(item.order for item in existing) + 1
        
    img_instance = ProductImage(product=product, order=max_order)
    img_instance.image.save(uploaded_file.name, processed_file, save=True)
    return img_instance

def delete_gallery_image(image_id):
    """
    Deletes the gallery image file from disk and model record.
    """
    from marketplace.models import ProductImage
    try:
        img = ProductImage.objects.get(pk=image_id)
        if img.image:
            delete_file_from_storage(img.image.name)
        img.delete()
    except ProductImage.DoesNotExist:
        pass

def save_download_file(product, uploaded_file):
    """
    Validates and uploads ZIP/RAR/7Z file. Creates/updates a single VersionHistory record for the product,
    guaranteeing automatic cleanup of any old file.
    """
    from marketplace.models import VersionHistory
    validate_archive_file(uploaded_file)
    
    # Fetch or create associated VersionHistory
    version_instance = product.versions.first()
    if not version_instance:
        version_instance = VersionHistory(
            product=product,
            version="1.0.0",
            changelog="Initial release mod file."
        )
    else:
        # Delete old file from storage if updating
        if version_instance.download_file:
            delete_file_from_storage(version_instance.download_file.name)
            
    version_instance.download_file.save(uploaded_file.name, uploaded_file, save=True)
    return version_instance.download_file.name

def delete_download_file(product):
    """
    Removes the download file from storage and clears the download_file field on the VersionHistory record.
    """
    version_instance = product.versions.first()
    if version_instance and version_instance.download_file:
        delete_file_from_storage(version_instance.download_file.name)
        version_instance.download_file = None
        version_instance.save()

def delete_file_from_storage(file_path):
    """
    Utility method to physically remove a file from Django storage, preventing orphans.
    """
    if file_path and default_storage.exists(file_path):
        default_storage.delete(file_path)
