import os
import sys
from django.core.wsgi import get_wsgi_application

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

django_app = get_wsgi_application()


def app(environ, start_response):
    """
    WSGI handler for Vercel Serverless Function deployment.
    When Vercel rewrites requests to '/api/index.py', the original URL path
    is passed in headers like HTTP_X_MATCHED_PATH, HTTP_X_VERCEL_PATH, or REQUEST_URI.
    We restore PATH_INFO to the client's actual requested route so Django URL resolver
    routes homepage ('/') and subpages correctly.
    """
    path_info = environ.get('PATH_INFO', '')
    if path_info in ('/api/index.py', '/api/index', '/api', ''):
        matched = (
            environ.get('HTTP_X_MATCHED_PATH') or
            environ.get('HTTP_X_VERCEL_PATH') or
            environ.get('HTTP_X_FORWARDED_PATH') or
            environ.get('REQUEST_URI') or
            environ.get('RAW_URI') or
            '/'
        )
        if matched:
            clean_path = matched.split('?')[0]
            if not clean_path.startswith('/api/index'):
                environ['PATH_INFO'] = clean_path
            else:
                environ['PATH_INFO'] = '/'

    return django_app(environ, start_response)


# Expose application as well for standard WSGI compatibility
application = app
