import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_wsgi_application()

# Safely synchronize administrative superuser credentials on WSGI container boot
try:
    from core.auto_admin import ensure_superuser_synced
    ensure_superuser_synced()
except Exception:
    pass
