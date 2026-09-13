import os
import mimetypes
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.views.static import serve
from core import supabase_storage


def media_serve(request, path):
    """
    Serves media files with Supabase Storage support and local fallback.
    - If local file exists in MEDIA_ROOT, serves it directly.
    - If Supabase Storage is configured, retrieves object from private bucket using Service Key
      and returns with proper MIME type and caching headers.
    """
    normalized_path = path.replace('\\', '/').lstrip('/')
    local_full_path = os.path.join(settings.MEDIA_ROOT, normalized_path)

    # 1. Check local filesystem first
    if os.path.exists(local_full_path) and os.path.isfile(local_full_path):
        return serve(request, normalized_path, document_root=settings.MEDIA_ROOT)

    # 2. Check Supabase Storage if configured
    if supabase_storage.is_configured():
        file_bytes = supabase_storage.download_file_bytes(normalized_path)
        if file_bytes is not None:
            content_type, _ = mimetypes.guess_type(normalized_path)
            content_type = content_type or 'application/octet-stream'

            # Cache locally to disk for subsequent instant loads if directory is writable
            try:
                os.makedirs(os.path.dirname(local_full_path), exist_ok=True)
                with open(local_full_path, 'wb') as f:
                    f.write(file_bytes)
            except Exception:
                pass

            response = HttpResponse(file_bytes, content_type=content_type)
            response['Cache-Control'] = 'public, max-age=86400'  # 24 hour browser cache
            return response

    raise Http404("Media file not found.")
