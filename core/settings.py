import os
import sys
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-secret-key-1234567890')

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# Environment & Vercel Detection
IS_VERCEL = os.getenv('VERCEL') == '1' or 'VERCEL' in os.environ

# ── Allowed Hosts & Domain Security ──────────────────────────────────────────
raw_allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
if raw_allowed_hosts:
    hosts = []
    for h in raw_allowed_hosts.split(','):
        h = h.strip()
        if not h:
            continue
        if h.startswith('https://'):
            h = h[8:]
        elif h.startswith('http://'):
            h = h[7:]
        h = h.split('/')[0].split(':')[0].strip()
        if h and h not in hosts:
            hosts.append(h)
    ALLOWED_HOSTS = hosts
else:
    ALLOWED_HOSTS = [
        'gtav-mods.vercel.app',
        '.vercel.app',
        'localhost',
        '127.0.0.1',
        '[::1]',
    ]
    if DEBUG:
        ALLOWED_HOSTS.append('*')

# Always ensure the deployed domains are present in ALLOWED_HOSTS
for default_host in ['gtav-mods.vercel.app', '.vercel.app', 'localhost', '127.0.0.1']:
    if default_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(default_host)

vercel_env_url = os.getenv('VERCEL_URL', '').strip()
if vercel_env_url:
    v_clean = vercel_env_url.replace('https://', '').replace('http://', '').split('/')[0].split(':')[0].strip()
    if v_clean and v_clean not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(v_clean)

# ── CSRF Trusted Origins ───────────────────────────────────────────────────
raw_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if raw_csrf_origins:
    origins = []
    for o in raw_csrf_origins.split(','):
        o = o.strip()
        if not o:
            continue
        if not o.startswith(('http://', 'https://')):
            o = f'https://{o}'
        o = o.rstrip('/')
        if o not in origins:
            origins.append(o)
    CSRF_TRUSTED_ORIGINS = origins
else:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost',
        'http://127.0.0.1',
        'https://gtav-mods.vercel.app',
        'https://*.vercel.app',
    ]

# Always ensure deployed origins are trusted for CSRF
for default_origin in ['https://gtav-mods.vercel.app', 'https://*.vercel.app']:
    if default_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(default_origin)

vercel_env_url = os.getenv('VERCEL_URL', '').strip()
if vercel_env_url:
    v_origin = f"https://{vercel_env_url.replace('https://', '').replace('http://', '').rstrip('/')}"
    if v_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(v_origin)



# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Custom apps
    'marketplace',
    'accounts',
    'orders',
    'blog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Whitenoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'marketplace.context_processors.cart_context', # Custom cart info globally
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
# ASGI_APPLICATION is omitted so Vercel native framework runner uses WSGI_APPLICATION

# Database Setup: dynamically load DATABASE_URL (PostgreSQL) or fallback to SQLite
is_collectstatic = any('collectstatic' in arg for arg in sys.argv)
raw_db_url = os.getenv('DATABASE_URL', '').strip()

if raw_db_url:
    import re
    # If Render internal hostname is passed (e.g. @dpg-xxxxxx-a/), it fails outside Render's private network.
    # Automatically rewrite to Render's public external hostname with SSL mode so Vercel can connect.
    match = re.search(r'@(dpg-[a-z0-9]+-[a-z0-9]+)([:/])', raw_db_url)
    if match:
        internal_host = match.group(1)
        render_region = os.getenv('RENDER_REGION', 'oregon').strip()
        external_host = f"{internal_host}.{render_region}-postgres.render.com"
        raw_db_url = raw_db_url.replace(f"@{internal_host}", f"@{external_host}")
        if 'sslmode=' not in raw_db_url:
            raw_db_url += ('&' if '?' in raw_db_url else '?') + 'sslmode=require'
    db_config = dj_database_url.parse(raw_db_url, conn_max_age=0 if IS_VERCEL else 600)
else:
    db_config = dj_database_url.config(conn_max_age=0 if IS_VERCEL else 600)

if not db_config:
    if is_collectstatic:
        db_config = dj_database_url.parse("sqlite:///:memory:")
    elif IS_VERCEL:
        # On Vercel, if DATABASE_URL is not yet set in environment variables, use /tmp/db.sqlite3
        # so serverless container never attempts to write to the read-only /var/task filesystem
        db_config = dj_database_url.parse("sqlite:////tmp/db.sqlite3")
    elif not DEBUG:
        raise RuntimeError("DATABASE_URL environment variable is required in production (DEBUG=False). Ephemeral SQLite fallback is disallowed.")
    else:
        db_config = dj_database_url.parse(f"sqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}")

DATABASES = {
    'default': db_config
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


# ── Supabase Storage Configuration (Private Bucket) ─────────────────────────
SUPABASE_URL = os.getenv('SUPABASE_URL', '').rstrip('/')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', os.getenv('SUPABASE_KEY', ''))
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'pawanmod-files')

# Whitenoise compression and Supabase/Local Storage backend
STORAGES = {
    "default": {
        "BACKEND": "core.supabase_backend.SupabaseStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
WHITENOISE_USE_FINDERS = True

# Media files (Product uploads, screenshots)
MEDIA_URL = '/media/'
if IS_VERCEL:
    # On Vercel, local storage is ephemeral /tmp only (permanent assets are stored on Supabase)
    MEDIA_ROOT = '/tmp/media'
else:
    MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.getenv('RENDER_DISK_PATH', os.path.join(BASE_DIR, 'media')))

# Ensure media storage directories exist (in /tmp on Vercel or locally)
try:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    os.makedirs(os.path.join(MEDIA_ROOT, 'products', 'images'), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_ROOT, 'products', 'gallery'), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_ROOT, 'products', 'files'), exist_ok=True)
except OSError:
    pass

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth URLs
LOGIN_URL = 'custom_admin:login'
LOGIN_REDIRECT_URL = 'custom_admin:dashboard'
LOGOUT_REDIRECT_URL = 'marketplace:home'

# ── Payment Gateways ────────────────────────────────────────────────────────
# Set these in your .env file. Leave blank to run in test/demo mode.
RAZORPAY_KEY_ID     = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
PAYPAL_CLIENT_ID    = os.getenv('PAYPAL_CLIENT_ID', '')

# ── Email Settings ──────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# ── Proxy & HTTPS Settings ──────────────────────────────────────────────────
# Honor the X-Forwarded-Proto header set by Vercel and upstream reverse proxies
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    # Vercel terminates SSL at its global edge. Defaults to False on Vercel to avoid redirect loops
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False' if IS_VERCEL else 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True



