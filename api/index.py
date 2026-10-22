import os
import sys
from django.core.wsgi import get_wsgi_application

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Vercel expects the WSGI app as 'app'
app = get_wsgi_application()
