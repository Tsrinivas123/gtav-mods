import sys
import logging
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseServerError, JsonResponse
from core.views_media import media_serve
from marketplace import views as marketplace_views

logger = logging.getLogger(__name__)


def health_status(request):
    """Safe system diagnostic endpoint that checks database connection without exposing secrets."""
    status = {"status": "ok", "app": "PawanMod", "database": "unknown"}
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            status["database"] = "connected" if row and row[0] == 1 else "unexpected"
    except Exception as e:
        status["database"] = f"error: {type(e).__name__}"
    return JsonResponse(status)


def custom_server_error(request):
    """Custom 500 handler that logs detailed traceback and returns a polished user page."""
    exc_type, exc_value, _ = sys.exc_info()
    error_summary = f"{exc_type.__name__}: {exc_value}" if exc_type else "Internal Server Error"
    logger.error(f"500 Internal Server Error: {error_summary}", exc_info=True)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Server Error (500) | PawanMod</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f1117; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }}
    .card {{ background: #1a1d27; border: 1px solid #2a2e3d; border-radius: 12px; padding: 40px; max-width: 500px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.4); }}
    h1 {{ color: #ff4757; margin-top: 0; font-size: 2rem; }}
    p {{ color: #a4b0be; line-height: 1.6; }}
    .btn {{ display: inline-block; background: #ff4757; color: #fff; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>500 - Server Error</h1>
    <p>Something went wrong on our servers. Our team has been notified and is working to resolve it.</p>
    <a href="/" class="btn">Return to Home</a>
    <!-- DIAGNOSTIC: {error_summary} -->
  </div>
</body>
</html>"""
    return HttpResponseServerError(html, content_type='text/html')


handler500 = 'core.urls.custom_server_error'

urlpatterns = [
    # Backward-compatible fallback in case edge proxies or cached requests hit /api/index
    re_path(r'^api/index(?:\.py)?/?$', marketplace_views.home, name='api_index_compat'),
    path('health/', health_status, name='health_status'),
    path('admin/', include('core.admin_urls', namespace='custom_admin')),
    path('custom-admin/', include('core.admin_urls', namespace='custom_admin_compat')),
    path('django-admin/', admin.site.urls),
    path('', include('marketplace.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
    path('blog/', include('blog.urls')),
    # Media files (Supabase Storage + local fallback)
    re_path(r'^media/(?P<path>.*)$', media_serve, name='media_serve'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
