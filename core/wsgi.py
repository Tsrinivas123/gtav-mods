import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
_django_app = get_wsgi_application()


def application(environ, start_response):
    path_info = environ.get('PATH_INFO', '')
    if path_info in ('/api/index.py', '/api/index', '/api'):
        matched = (
            environ.get('HTTP_X_MATCHED_PATH') or
            environ.get('HTTP_X_VERCEL_PATH') or
            environ.get('HTTP_X_FORWARDED_PATH') or
            environ.get('REQUEST_URI') or
            environ.get('RAW_URI')
        )
        if matched:
            clean_path = matched.split('?')[0]
            if not clean_path.startswith('/api/index'):
                environ['PATH_INFO'] = clean_path
            else:
                environ['PATH_INFO'] = '/'
    return _django_app(environ, start_response)


app = application

# Safely synchronize administrative superuser credentials on WSGI container boot
try:
    from core.auto_admin import ensure_superuser_synced
    ensure_superuser_synced()
except Exception:
    pass
