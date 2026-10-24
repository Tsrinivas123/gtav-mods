import os
import mimetypes
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.views.static import serve
from core import supabase_storage


def media_serve(request, path):
    """
    Serves public media files (images, banners, thumbnails) with Supabase Storage support and local fallback.
    Private mod archives (e.g. .zip, .rar, .7z files under products/files/) are strictly blocked
    from direct media access and must be downloaded via the authenticated download endpoint.
    """
    normalized_path = path.replace('\\', '/').lstrip('/')

    # Block direct access to mod archives and protected product files
    archive_exts = ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2')
    if normalized_path.startswith('products/files/') or normalized_path.lower().endswith(archive_exts):
        raise Http404("Direct access to private archives is forbidden.")

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

            # Cache locally to disk for subsequent instant loads in local dev only (skipped on Vercel)
            is_vercel = getattr(settings, 'IS_VERCEL', False) or os.getenv('VERCEL') == '1' or 'VERCEL' in os.environ
            if not is_vercel:
                try:
                    os.makedirs(os.path.dirname(local_full_path), exist_ok=True)
                    with open(local_full_path, 'wb') as f:
                        f.write(file_bytes)
                except OSError:
                    pass

            response = HttpResponse(file_bytes, content_type=content_type)
            response['Cache-Control'] = 'public, max-age=86400'  # 24 hour browser cache
            return response

    raise Http404("Media file not found.")
