from django.core.files.storage import default_storage
from core.supabase_backend import SupabaseStorage


def get_private_storage():
    """Callable for Django migrations and private file fields."""
    return default_storage
