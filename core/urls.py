from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from core.views_media import media_serve
from marketplace import views as marketplace_views

urlpatterns = [
    # Backward-compatible fallback in case edge proxies or cached requests hit /api/index
    re_path(r'^api/index(?:\.py)?/?$', marketplace_views.home, name='api_index_compat'),
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

