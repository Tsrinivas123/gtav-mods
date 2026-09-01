from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile

class AccountFlowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_tester',
            email='admin@example.com',
            password='Password123!'
        )

    def test_customer_login_redirects_to_store(self):
        """Verify public customer login route redirects safely to store."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 302)

    def test_customer_register_redirects_to_store(self):
        """Verify public customer register route redirects safely to store."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 302)

    def test_superuser_admin_login(self):
        """Verify superuser can log into /admin/login/ and redirect to /admin/."""
        response = self.client.post(reverse('custom_admin:login'), {
            'username': 'admin_tester',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('custom_admin:dashboard'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_superuser_env_authentication_and_admin_redirect(self):
        """Verify superuser synced from environment can authenticate via admin login."""
        from core.auto_admin import ensure_superuser_synced
        ensure_superuser_synced()

        response = self.client.post(reverse('custom_admin:login'), {
            'username': 'Tushar',
            'password': 'luffy123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('custom_admin:dashboard'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_user_logout(self):
        """Verify logging out clears session."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)
