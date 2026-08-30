from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile

class AccountFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='Password123!'
        )

    def test_login_page_loads(self):
        """Verify login/register page renders status 200 and contains form elements."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")
        self.assertContains(response, "Register")

    def test_user_login_success(self):
        """Verify valid user login redirects to dashboard or requested page."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_user_registration_success(self):
        """Verify new user registration creates user and logs them in."""
        response = self.client.post(reverse('accounts:register'), {
            'email': 'newuser@example.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_user_dashboard_access(self):
        """Verify user dashboard loads for authenticated users and redirects unauthenticated users."""
        # Anonymous request -> redirect to login
        anon_response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(anon_response.status_code, 302)

        # Authenticated request -> 200
        self.client.force_login(self.user)
        auth_response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(auth_response.status_code, 200)
        self.assertContains(auth_response, "Account details")

    def test_profile_update(self):
        """Verify updating billing address on profile works properly."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:profile_update'), {
            'email': 'updated@example.com',
            'billing_address': '456 Cyberpunk Blvd, Night City'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.billing_address, '456 Cyberpunk Blvd, Night City')

    def test_user_logout(self):
        """Verify logging out clears session."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_superuser_env_authentication_and_admin_redirect(self):
        """Verify superuser synced from environment can authenticate and is redirected to custom admin dashboard."""
        from core.auto_admin import ensure_superuser_synced
        ensure_superuser_synced()

        response = self.client.post(reverse('accounts:login'), {
            'username': 'Tushar',
            'password': 'luffy123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('custom_admin:dashboard'))
        self.assertTrue('_auth_user_id' in self.client.session)
