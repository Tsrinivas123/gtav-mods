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

        # 1. Unauthorized user tries to download paid mod
        r_unauth = anon_client.get(f'/orders/download/{self.version.id}/')
        self.assertEqual(r_unauth.status_code, 302)
        self.assertIn(self.product.slug, r_unauth.url)

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
