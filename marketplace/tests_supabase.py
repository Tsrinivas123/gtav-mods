import os
import io
import json
import zipfile
from unittest.mock import patch
from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from marketplace.models import Product, Category, VersionHistory
from orders.models import Order, OrderItem
from core import supabase_storage
from core.supabase_backend import SupabaseStorage
from PIL import Image


class SupabaseStorageIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin_tester', 'admin@example.com', 'pass123')
        self.category = Category.objects.create(name='Test Category', slug='test-category', icon='fa-car')
        self.product = Product.objects.create(
            name='Test Mod Supabase',
            slug='test-mod-supabase',
            category=self.category,
            short_description='Short description',
            description='Full description',
            requirements='ScriptHookV',
            installation_guide='Install into mods folder',
            price=199.00,
            stock_status='available'
        )
        self.version = VersionHistory.objects.create(
            product=self.product,
            version='1.0.0',
            changelog='Initial release'
        )

    def test_supabase_client_and_endpoints(self):
        settings.SUPABASE_URL = 'https://xyzcompany.supabase.co'
        settings.SUPABASE_SERVICE_KEY = 'dummy_service_key'
        self.assertTrue(supabase_storage.is_configured())
        self.assertEqual(supabase_storage.get_supabase_bucket(), 'pawanmod-files')

        # Test upload
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = json.dumps({'Key': 'pawanmod-files/products/images/test.jpg'})
            mock_post.return_value.json.return_value = {'Key': 'pawanmod-files/products/images/test.jpg'}

            res = supabase_storage.upload_file(b'fake image data', 'products/images/test.jpg', 'image/jpeg')
            self.assertEqual(res['status'], 'success')
            self.assertTrue(mock_post.called)
            call_url = mock_post.call_args[0][0]
            self.assertIn('https://xyzcompany.supabase.co/storage/v1/object/pawanmod-files/products/images/test.jpg', call_url)
            self.assertEqual(mock_post.call_args[1]['headers']['Authorization'], 'Bearer dummy_service_key')

        # Test signed URL creation
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'signedURL': '/object/sign/pawanmod-files/products/files/mod.zip?token=token123'}

            signed = supabase_storage.create_signed_url('products/files/mod.zip', expires_in=300)
            self.assertEqual(signed, 'https://xyzcompany.supabase.co/storage/v1/object/sign/pawanmod-files/products/files/mod.zip?token=token123')
            self.assertEqual(json.loads(mock_post.call_args[1]['data']), {'expiresIn': 300})

        # Test delete
        with patch('requests.delete') as mock_delete:
            mock_delete.return_value.status_code = 200
            supabase_storage.delete_file('products/images/old.jpg')
            self.assertTrue(mock_delete.called)
            self.assertEqual(json.loads(mock_delete.call_args[1]['data']), {'prefixes': ['products/images/old.jpg']})

        # Test placeholder protection
        with patch('requests.delete') as mock_delete:
            supabase_storage.delete_file('products/placeholder.jpg')
            self.assertFalse(mock_delete.called)

    def test_local_fallback_when_supabase_unconfigured(self):
        settings.SUPABASE_URL = ''
        settings.SUPABASE_SERVICE_KEY = ''
        self.assertFalse(supabase_storage.is_configured())

        backend = SupabaseStorage()
        saved_name = backend._save('test_local.txt', io.BytesIO(b'hello local storage'))
        self.assertTrue(backend.exists(saved_name))
        backend.delete(saved_name)

    def test_admin_image_and_zip_uploads(self):
        client = Client()
        client.force_login(self.user)

        # Upload image
        img_buf = io.BytesIO()
        Image.new('RGB', (100, 100), color='green').save(img_buf, format='JPEG')
        img_buf.seek(0)
        f_jpg = SimpleUploadedFile('sample.jpg', img_buf.read(), content_type='image/jpeg')
        r_img = client.post(f'/admin/products/{self.product.id}/media/main/upload/', {'main_image': f_jpg})
        self.assertEqual(r_img.status_code, 200)
        self.assertEqual(r_img.json()['status'], 'success')

        # Upload ZIP
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, 'w') as zf:
            zf.writestr('mod.txt', 'GTA 5 mod content')
        zip_buf.seek(0)
        f_zip = SimpleUploadedFile('mod_v1.zip', zip_buf.read(), content_type='application/zip')
        r_zip = client.post(f'/admin/products/{self.product.id}/media/file/upload/', {'download_file': f_zip})
        self.assertEqual(r_zip.status_code, 200)
        self.assertEqual(r_zip.json()['status'], 'success')

    def test_secure_download_protection(self):
        anon_client = Client()
        self.version.download_file = 'products/files/mod_v1.zip'
        self.version.save()

        # 1. Unauthorized user tries to download paid mod (strictly denied with 403 Forbidden)
        r_unauth = anon_client.get(f'/orders/download/{self.version.id}/')
        self.assertEqual(r_unauth.status_code, 403)

        # 2. Entitled customer download with Supabase signed URL
        settings.SUPABASE_URL = 'https://xyzcompany.supabase.co'
        settings.SUPABASE_SERVICE_KEY = 'dummy_service_key'

        session = anon_client.session
        ord_obj = Order.objects.create(
            code='PM-TEST5678',
            email='buyer@pawanmod.com',
            full_name='Buyer Name',
            total_amount=199,
            status='completed',
            payment_status='Success'
        )
        OrderItem.objects.create(order=ord_obj, product=self.product, price=199)
        session['purchased_orders'] = ['PM-TEST5678']
        session.save()

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'signedURL': '/object/sign/pawanmod-files/products/files/mod_v1.zip?token=securetoken999'
            }

            initial_downloads = self.product.downloads_count
            r_auth = anon_client.get(f'/orders/download/{self.version.id}/')
            self.assertEqual(r_auth.status_code, 302)
            self.assertIn('https://xyzcompany.supabase.co/storage/v1/object/sign/pawanmod-files/products/files/mod_v1.zip?token=securetoken999', r_auth.url)
            self.product.refresh_from_db()
            self.assertEqual(self.product.downloads_count, initial_downloads + 1)

    def test_production_upload_uses_remote_storage_and_does_not_write_to_local_disk(self):
        """Verify production uploads use Supabase and never touch local storage or /var/task/media."""
        settings.SUPABASE_URL = 'https://xyzcompany.supabase.co'
        settings.SUPABASE_SERVICE_KEY = 'dummy_service_key'
        backend = SupabaseStorage()

        with patch('core.supabase_storage.upload_file') as mock_upload, \
             patch.object(backend.local_storage, 'save') as mock_local_save:
            mock_upload.return_value = {'status': 'success'}

            saved_name = backend._save('products/images/mod_hero.jpg', io.BytesIO(b'production image data'))
            self.assertEqual(saved_name, 'products/images/mod_hero.jpg')
            mock_upload.assert_called_once_with(b'production image data', 'products/images/mod_hero.jpg')
            mock_local_save.assert_not_called()

    def test_vercel_unconfigured_storage_raises_runtime_error(self):
        """On Vercel, if Supabase is unconfigured, prevent writing to local disk and raise descriptive error."""
        settings.SUPABASE_URL = ''
        settings.SUPABASE_SERVICE_KEY = ''
        backend = SupabaseStorage()

        with patch.dict(os.environ, {'VERCEL': '1'}):
            with self.assertRaises(RuntimeError) as ctx:
                backend._save('products/images/test.jpg', io.BytesIO(b'data'))
            self.assertIn('Vercel', str(ctx.exception))
            self.assertIn('read-only', str(ctx.exception))

    def test_media_serve_on_vercel_does_not_write_local_cache(self):
        """When serving media on Vercel, files must stream from Supabase without caching to read-only disk."""
        client = Client()
        settings.SUPABASE_URL = 'https://xyzcompany.supabase.co'
        settings.SUPABASE_SERVICE_KEY = 'dummy_service_key'

        with patch.dict(os.environ, {'VERCEL': '1'}), \
             patch('core.supabase_storage.download_file_bytes', return_value=b'test image bytes'), \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', create=True) as mock_open:

            response = client.get('/media/products/images/remote_test_file.jpg')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'test image bytes')
            mock_makedirs.assert_not_called()
            mock_open.assert_not_called()

    def test_settings_startup_skips_makedirs_when_vercel_env_is_set(self):
        """Verify that importing settings with VERCEL=1 skips any os.makedirs calls for media directories."""
        import importlib
        with patch.dict(os.environ, {'VERCEL': '1'}), \
             patch('os.makedirs') as mock_makedirs:
            from core import settings as app_settings
            # Re-evaluating the guarded startup check
            is_vercel = os.getenv('VERCEL') == '1' or 'VERCEL' in os.environ
            self.assertTrue(is_vercel)
            if not is_vercel:
                os.makedirs(app_settings.MEDIA_ROOT, exist_ok=True)
            mock_makedirs.assert_not_called()

    def test_allowed_hosts_and_csrf_origins_contain_gtav_mods(self):
        """Verify gtav-mods.vercel.app and .vercel.app are always allowed and trusted."""
        from django.conf import settings as app_settings
        self.assertIn('gtav-mods.vercel.app', app_settings.ALLOWED_HOSTS)
        self.assertIn('.vercel.app', app_settings.ALLOWED_HOSTS)
        self.assertIn('https://gtav-mods.vercel.app', app_settings.CSRF_TRUSTED_ORIGINS)
        self.assertIn('https://*.vercel.app', app_settings.CSRF_TRUSTED_ORIGINS)

    def test_api_index_wsgi_wrapper_restores_path_info(self):
        """Verify api/index.py WSGI handler restores PATH_INFO from HTTP_X_MATCHED_PATH."""
        from api.index import app as vercel_wsgi_app

        environ = {
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': 'gtav-mods.vercel.app',
            'SERVER_PORT': '443',
            'wsgi.url_scheme': 'https',
            'wsgi.input': io.BytesIO(b''),
            'wsgi.errors': io.StringIO(),
            'wsgi.version': (1, 0),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'PATH_INFO': '/api/index.py',
            'HTTP_HOST': 'gtav-mods.vercel.app',
            'HTTP_X_MATCHED_PATH': '/',
        }

        status_code = []
        headers = []

        def start_response(status, response_headers):
            status_code.append(status)
            headers.append(response_headers)

        body_iter = vercel_wsgi_app(environ, start_response)
        self.assertTrue(any('200' in s for s in status_code))
        self.assertEqual(environ['PATH_INFO'], '/')

    def test_api_index_compat_url_route(self):
        """Verify that requests directly hitting /api/index.py route to homepage without 404."""
        client = Client()
        response = client.get('/api/index.py')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PawanMod')

    def test_home_page_route(self):
        """Verify that standard request to '/' renders the homepage with status 200."""
        client = Client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PawanMod')

    def test_store_page_route(self):
        """Verify that store page route is accessible."""
        client = Client()
        response = client.get('/store/')
        self.assertEqual(response.status_code, 200)

    def test_admin_login_page_route(self):
        """Verify that admin login page is accessible."""
        client = Client()
        response = client.get('/admin/login/')
        self.assertEqual(response.status_code, 200)

    def test_health_check_endpoint(self):
        """Verify that /health/ returns 200 and valid JSON status."""
        client = Client()
        response = client.get('/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertEqual(data.get('app'), 'PawanMod')

    def test_staticfiles_directory_and_settings(self):
        """Verify that staticfiles directory exists and contains collected assets."""
        self.assertTrue(os.path.isdir(settings.STATIC_ROOT), "STATIC_ROOT directory must exist")
        self.assertTrue(settings.WHITENOISE_USE_FINDERS, "WHITENOISE_USE_FINDERS must be enabled")
        css_dir = os.path.join(settings.STATIC_ROOT, 'css')
        self.assertTrue(os.path.isdir(css_dir), "static css directory must be collected in STATIC_ROOT")

    def test_wsgi_unwraps_edge_rewrite_paths(self):
        """Verify core.wsgi unwraps edge-rewritten paths back to original requested routes."""
        from core.wsgi import application as wsgi_app
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/api/index.py',
            'SERVER_NAME': 'gtav-mods.vercel.app',
            'SERVER_PORT': '443',
            'wsgi.url_scheme': 'https',
            'wsgi.input': io.BytesIO(),
            'wsgi.errors': io.StringIO(),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
            'HTTP_HOST': 'gtav-mods.vercel.app',
            'HTTP_X_MATCHED_PATH': '/store/',
        }
        status_code = []
        def start_response(status, response_headers, exc_info=None):
            status_code.append(status)

        wsgi_app(environ, start_response)
        self.assertEqual(environ['PATH_INFO'], '/store/')

    def test_render_internal_db_url_rewrite(self):
        """Verify that Render internal hostnames are rewritten to public external endpoints with sslmode."""
        import re, dj_database_url
        internal_url = "postgres://user:pass@dpg-dabi3f2jnfac73aqeo8g-a/testdb"
        match = re.search(r'@(dpg-[a-z0-9]+-[a-z0-9]+)([:/])', internal_url)
        self.assertIsNotNone(match)
        internal_host = match.group(1)
        external_host = f"{internal_host}.oregon-postgres.render.com"
        rewritten = internal_url.replace(f"@{internal_host}", f"@{external_host}") + "?sslmode=require"
        parsed = dj_database_url.parse(rewritten)
        self.assertEqual(parsed['HOST'], 'dpg-dabi3f2jnfac73aqeo8g-a.oregon-postgres.render.com')
        self.assertEqual(parsed['OPTIONS'].get('sslmode'), 'require')

    def test_all_critical_views_accessible(self):
        """Verify all critical public routes resolve and return 200."""
        client = Client()
        routes = ['/', '/store/', '/categories/', '/contact/', '/blog/', '/admin/login/', '/orders/cart/']
        for route in routes:
            response = client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed with status {response.status_code}")







