from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from marketplace.models import Category, Product
from orders.models import Order, Coupon

class CompleteUserAndAdminFlowTests(TestCase):
    def setUp(self):
        # Create test superuser/staff for admin tests
        self.admin = User.objects.create_superuser('admin_tester', 'admin@pawanmod.com', 'AdminPass123!')
        
        # Create regular user
        self.user = User.objects.create_user('customer_tester', 'customer@pawanmod.com', 'CustomerPass123!')
        
        # Create test category and product
        self.category = Category.objects.create(name='Supercars', icon='fa-car', description='Fast cars')
        self.product = Product.objects.create(
            name='Bugatti Chiron Mod',
            category=self.category,
            short_description='Super fast car mod',
            description='Detailed Bugatti Chiron GTA 5 replace mod with custom tuning and HQ interior.',
            requirements='ScriptHookV, OpenIV',
            installation_guide='Extract to mods/update/x64/dlcpacks',
            price=25.00,
            old_price=35.00,
            stock_status='available'
        )

    def test_full_user_checkout_flow(self):
        """Test complete user journey: Home -> Store -> Product -> Cart -> Checkout -> Payment -> Complete"""
        # 1. Home page
        res_home = self.client.get(reverse('marketplace:home'))
        self.assertEqual(res_home.status_code, 200)
        self.assertContains(res_home, 'Bugatti Chiron Mod')

        # 2. Store page
        res_store = self.client.get(reverse('marketplace:store'))
        self.assertEqual(res_store.status_code, 200)
        self.assertContains(res_store, 'Bugatti Chiron Mod')

        # 3. Product detail page
        res_detail = self.client.get(reverse('marketplace:product_detail', args=[self.product.slug]))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, 'Bugatti Chiron Mod')

        # 4. Add product to Cart
        res_add_cart = self.client.post(reverse('orders:cart_add', args=[self.product.id]), follow=True)
        self.assertEqual(res_add_cart.status_code, 200)
        self.assertContains(res_add_cart, 'Bugatti Chiron Mod')

        # 5. View Cart
        res_cart = self.client.get(reverse('orders:cart'))
        self.assertEqual(res_cart.status_code, 200)
        self.assertContains(res_cart, 'Proceed to Checkout')

        # 6. View Checkout
        res_checkout = self.client.get(reverse('orders:checkout'))
        self.assertEqual(res_checkout.status_code, 200)
        self.assertContains(res_checkout, 'Billing Details')

        # 7. Post Checkout Details -> Order creation
        res_post_checkout = self.client.post(reverse('orders:checkout'), {
            'full_name': 'Test Customer',
            'email': 'customer@pawanmod.com',
            'phone': '9876543210',
            'city': 'Mumbai',
            'country': 'IN',
            'billing_address': '123 Marine Drive',
            'payment_method': 'UPI'
        })
        self.assertEqual(res_post_checkout.status_code, 302)
        order = Order.objects.latest('id')
        self.assertEqual(order.full_name, 'Test Customer')

        # 8. Payment Page
        payment_url = reverse('orders:payment_gate', args=[order.code])
        res_payment = self.client.get(payment_url)
        self.assertEqual(res_payment.status_code, 200)
        self.assertContains(res_payment, 'UPI QR Code Payment')

        # 9. Verify / Complete Payment
        complete_url = reverse('orders:payment_complete')
        res_complete = self.client.post(complete_url, {
            'order_code': order.code,
            'payment_id': 'upi_test_123456',
            'gateway': 'UPI'
        }, content_type='application/json')
        self.assertEqual(res_complete.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'Success')

    def test_full_admin_flow(self):
        """Test admin flow: Login -> Dashboard -> Products List -> Add -> Edit -> Delete -> Logout"""
        # 1. Access admin dashboard (requires login)
        res_unauth = self.client.get(reverse('custom_admin:dashboard'))
        self.assertEqual(res_unauth.status_code, 302)

        # 2. Login as admin
        self.client.force_login(self.admin)
        res_dash = self.client.get(reverse('custom_admin:dashboard'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, 'Dashboard')

        # 3. View products list
        res_prods = self.client.get(reverse('custom_admin:products'))
        self.assertEqual(res_prods.status_code, 200)
        self.assertContains(res_prods, 'Bugatti Chiron Mod')

        # 4. Add new product
        res_add = self.client.post(reverse('custom_admin:product_add'), {
            'name': 'Pagani Huayra Mod',
            'category': self.category.id,
            'short_description': 'Italian hypercar',
            'description': 'Pagani Huayra GTA V replace vehicle mod with working dials.',
            'requirements': 'ScriptHookV, OpenIV',
            'installation_guide': 'Extract to dlcpacks',
            'price': '30.00',
            'old_price': '40.00',
            'stock_status': 'available'
        })
        self.assertEqual(res_add.status_code, 302)
        new_prod = Product.objects.get(name='Pagani Huayra Mod')

        # 5. Edit product
        res_edit = self.client.post(reverse('custom_admin:product_edit', args=[new_prod.id]), {
            'name': 'Pagani Huayra Mod Updated',
            'category': self.category.id,
            'short_description': 'Updated short desc',
            'description': 'Updated description.',
            'requirements': 'ScriptHookV, OpenIV',
            'installation_guide': 'Extract to dlcpacks',
            'price': '35.00',
            'old_price': '45.00',
            'stock_status': 'available'
        })
        self.assertEqual(res_edit.status_code, 302)
        new_prod.refresh_from_db()
        self.assertEqual(new_prod.name, 'Pagani Huayra Mod Updated')

        # 6. Delete product
        res_del = self.client.post(reverse('custom_admin:product_delete', args=[new_prod.id]))
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(Product.objects.filter(id=new_prod.id).exists())

        # 7. Logout
        self.client.logout()
        res_logout_dash = self.client.get(reverse('custom_admin:dashboard'))
        self.assertEqual(res_logout_dash.status_code, 302)

    def test_page_availability(self):
        """Test public routes availability"""
        routes = [
            'marketplace:home',
            'marketplace:store',
            'marketplace:contact',
            'blog:post_list',
        ]
        for r in routes:
            res = self.client.get(reverse(r))
            self.assertEqual(res.status_code, 200, f"Route {r} failed with status {res.status_code}")

    def test_dedicated_admin_login_page_renders(self):
        """Verify custom admin login page renders status 200."""
        response = self.client.get(reverse('custom_admin:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Portal Login")

    def test_admin_login_with_superuser_credentials(self):
        """Verify superuser can log in directly at custom_admin:login and is redirected to dashboard."""
        response = self.client.post(reverse('custom_admin:login'), {
            'username': 'admin_tester',
            'password': 'AdminPass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('custom_admin:dashboard'))
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_admin_login_denied_for_regular_user(self):
        """Verify regular users cannot log into the custom admin panel and see an error."""
        response = self.client.post(reverse('custom_admin:login'), {
            'username': 'customer_tester',
            'password': 'CustomerPass123!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Access denied")

    def test_unauthenticated_admin_redirect_to_custom_admin_login(self):
        """Verify unauthenticated requests to /custom-admin/ redirect to /custom-admin/login/."""
        response = self.client.get(reverse('custom_admin:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('custom_admin:login'))

    def test_admin_logout_redirects_to_custom_admin_login(self):
        """Verify admin logout redirects to custom_admin:login."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('custom_admin:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('custom_admin:login'))
