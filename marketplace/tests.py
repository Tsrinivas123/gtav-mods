from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Product

class MarketplaceModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Vehicles",
            icon="fa-car",
            description="hypercars models"
        )
        self.product = Product.objects.create(
            name="Mod Test",
            category=self.category,
            short_description="Short desc",
            description="Long description details",
            requirements="ScriptHookV",
            installation_guide="Copy and paste files",
            price=10.00,
            old_price=20.00,
            downloads_count=5
        )

    def test_category_slug_generation(self):
        """Verify slugs generate automatically when category saves."""
        self.assertEqual(self.category.slug, "vehicles")

    def test_product_discount_math(self):
        """Verify discount percentage computes correctly from old and new prices."""
        self.assertEqual(self.product.discount_percentage, 50)

    def test_home_page_view(self):
        """Verify home page loads returns status 200."""
        # Ensure available products show, draft doesn't
        self.product.stock_status = 'available'
        self.product.save()
        
        draft = Product.objects.create(
            name="Draft Mod",
            category=self.category,
            short_description="Short desc",
            description="Long description details",
            price=15.00,
            stock_status='coming_soon'
        )
        
        response = self.client.get(reverse('marketplace:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mod Test")
        self.assertNotContains(response, "Draft Mod")

    def test_store_filters_view(self):
        """Verify store catalog displays items correctly."""
        self.product.stock_status = 'available'
        self.product.save()
        
        response = self.client.get(reverse('marketplace:store'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mod Test")

    def test_draft_product_invisible_public(self):
        """Verify draft product is not listed on the storefront and returns 404 on detail page for guest users."""
        draft_product = Product.objects.create(
            name="Super Draft",
            category=self.category,
            short_description="Draft",
            description="Long draft desc",
            price=10.00,
            stock_status='coming_soon'
        )
        # Verify it doesn't appear in store view
        response = self.client.get(reverse('marketplace:store'))
        self.assertNotContains(response, "Super Draft")
        
        # Verify it returns 404 for anonymous users on detail page
        detail_url = reverse('marketplace:product_detail', args=[draft_product.slug])
        response_detail = self.client.get(detail_url)
        self.assertEqual(response_detail.status_code, 404)

    def test_search_icontains_fields(self):
        """Verify case-insensitive search queries match name, description, and category."""
        self.product.stock_status = 'available'
        self.product.save()
        
        # Match by name
        response = self.client.get(reverse('marketplace:store') + '?search=MoD')
        self.assertContains(response, "Mod Test")
        
        # Match by category
        response = self.client.get(reverse('marketplace:store') + '?search=vehiCl')
        self.assertContains(response, "Mod Test")

    def test_category_form_unique_and_slug(self):
        """Verify CategoryForm validates duplicates and generates slugs."""
        from core.admin_forms import CategoryAdminForm
        
        # Test case-insensitive duplicate name
        form = CategoryAdminForm(data={
            'name': 'vEhIcLeS',
            'slug': 'vehicles',
            'icon': 'fa-car',
            'status': 'active'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
        # Test empty slug gets auto generated
        form2 = CategoryAdminForm(data={
            'name': 'New Category',
            'slug': '',
            'icon': 'fa-folder',
            'status': 'active'
        })
        self.assertTrue(form2.is_valid())
        self.assertEqual(form2.cleaned_data['slug'], 'new-category')

    def test_category_delete_protection_migration(self):
        """Verify category deletion safety migrates products to another category."""
        target_category = Category.objects.create(
            name="Scripts",
            icon="fa-file-code",
            description="LUA and DLL scripts"
        )
        # Verify self.product is currently in self.category
        self.assertEqual(self.product.category, self.category)
        
        # Post to delete view with target category
        delete_url = reverse('custom_admin:category_delete', args=[self.category.id])
        
        # Simulate log in as staff
        staff_user = User.objects.create_superuser('admin_user', 'admin@test.com', 'pass123')
        self.client.force_login(staff_user)
        
        response = self.client.post(delete_url, {'target_category': target_category.id})
        self.assertEqual(response.status_code, 302)
        
        # Verify category was deleted
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())
        
        # Verify product was migrated
        self.product.refresh_from_db()
        self.assertEqual(self.product.category, target_category)

    def test_inactive_category_filtering(self):
        """Verify inactive categories hide their products on public storefront."""
        self.product.stock_status = 'available'
        self.product.save()
        
        # Verify active works first
        response = self.client.get(reverse('marketplace:store'))
        self.assertContains(response, "Mod Test")
        
        # Make category inactive
        self.category.status = 'inactive'
        self.category.save()
        
        # Verify it no longer appears in storefront store catalog
        response = self.client.get(reverse('marketplace:store'))
        self.assertNotContains(response, "Mod Test")
        
        # Verify category detail page returns 404
        response_detail = self.client.get(reverse('marketplace:category_detail', args=[self.category.slug]))
        self.assertEqual(response_detail.status_code, 404)
        
        # Verify product detail page returns 404
        response_prod = self.client.get(reverse('marketplace:product_detail', args=[self.product.slug]))
        self.assertEqual(response_prod.status_code, 404)

    def test_contact_form_submission_success(self):
        """Verify submitting contact support form creates ticket and redirects safely without 500 error."""
        session = self.client.session
        session['support_captcha_answer'] = 15
        session.save()

        response = self.client.post(reverse('marketplace:contact'), {
            'name': 'Jane Doe',
            'email': 'janedoe@example.com',
            'category': 'vehicles',
            'message': 'This is a test message for contact support verification.',
            'captcha_answer': '15'
        })
        self.assertIn(response.status_code, [200, 302])
        from marketplace.models import ContactMessage
        self.assertTrue(ContactMessage.objects.filter(email='janedoe@example.com').exists())

    def test_createsuperuser_if_none_creates_and_updates(self):
        """Verify createsuperuser_if_none creates and safely updates superuser credentials."""
        from django.core.management import call_command
        from django.contrib.auth.models import User
        
        # Test creation
        call_command('createsuperuser_if_none')
        self.assertTrue(User.objects.filter(username__iexact='Tushar', is_superuser=True).exists())

        # Test updating password / credentials
        call_command('createsuperuser_if_none')
        user = User.objects.get(username__iexact='Tushar')
        self.assertTrue(user.check_password('luffy123'))

    def test_product_without_image_navigation(self):
        """Verify product without an uploaded image renders detail links correctly and detail view returns 200 OK."""
        self.product.stock_status = 'available'
        self.product.save()

        # Create second product without image
        product2 = Product.objects.create(
            name="Cyber Weapon Pack",
            category=self.category,
            short_description="Custom HD weapon skins",
            description="Detailed custom rifle skins",
            price=25.00,
            stock_status='available'
        )

        detail_url1 = reverse('marketplace:product_detail', args=[self.product.slug])
        detail_url2 = reverse('marketplace:product_detail', args=[product2.slug])

        response_store = self.client.get(reverse('marketplace:store'))
        self.assertEqual(response_store.status_code, 200)

        # 1. Fallback image box rendered for missing images
        self.assertContains(response_store, 'class="fallback-img"')

        # 2 & 3 & 6. Verify image area, title, and card container render distinct detail URLs for product 1 and product 2
        self.assertContains(response_store, detail_url1)
        self.assertContains(response_store, detail_url2)

        # 4 & 5. Verify Add to Cart and Buy Now form targets
        cart_add_url1 = reverse('orders:cart_add', args=[self.product.id])
        cart_add_url2 = reverse('orders:cart_add', args=[product2.id])
        self.assertContains(response_store, cart_add_url1)
        self.assertContains(response_store, cart_add_url2)
        self.assertContains(response_store, 'name="checkout_direct"')

        # Check detail view for product without image renders 200 OK
        response_detail1 = self.client.get(detail_url1)
        self.assertEqual(response_detail1.status_code, 200)
        self.assertContains(response_detail1, "Mod Test")

        response_detail2 = self.client.get(detail_url2)
        self.assertEqual(response_detail2.status_code, 200)
        self.assertContains(response_detail2, "Cyber Weapon Pack")

    def test_breadcrumb_category_rendering_and_links(self):
        """FIX 1: Verify breadcrumb renders actual category name and valid links, not raw template syntax."""
        self.product.stock_status = 'available'
        self.product.save()

        detail_url = reverse('marketplace:product_detail', args=[self.product.slug])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        # Must not contain literal template tags
        self.assertNotContains(response, '{{ product.category.name }}')
        self.assertNotContains(response, '{{')

        # Must contain category name and valid category detail link
        self.assertContains(response, self.category.name)
        cat_url = reverse('marketplace:category_detail', args=[self.category.slug])
        self.assertContains(response, cat_url)

    def test_rating_accuracy_empty_and_populated_states(self):
        """FIX 4: Verify rating displays 'No reviews yet' when empty and computes actual average when populated."""
        self.product.stock_status = 'available'
        self.product.save()

        # When no reviews exist:
        self.assertIsNone(self.product.average_rating)
        self.assertEqual(self.product.rating_breakdown, [])

        detail_url = reverse('marketplace:product_detail', args=[self.product.slug])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        # Must show empty state, NOT fabricated 4.5 or hardcoded 85%
        self.assertContains(response, "No reviews yet")
        self.assertNotContains(response, "4.5")
        self.assertNotContains(response, "85%")

        # Add genuine review
        from marketplace.models import Review
        Review.objects.create(
            product=self.product,
            reviewer_name="Verified Buyer",
            rating=5,
            title="Awesome Mod",
            content="Great quality!"
        )

        self.assertEqual(self.product.average_rating, 5.0)
        self.assertEqual(self.product.reviews_count, 1)

        response_reviewed = self.client.get(detail_url)
        self.assertEqual(response_reviewed.status_code, 200)
        self.assertContains(response_reviewed, "Awesome Mod")
        self.assertContains(response_reviewed, "5.0")
        self.assertContains(response_reviewed, "100%")

    def test_guest_review_submission_verification(self):
        """FIX 3: Verify guest review submission enforces purchase verification and prevents duplicates."""
        from orders.models import Order, OrderItem
        from marketplace.models import Review

        self.product.stock_status = 'available'
        self.product.save()

        review_url = reverse('marketplace:submit_review', args=[self.product.slug])

        # 1. Unauthenticated guest without order details fails
        resp_fail = self.client.post(review_url, {
            'order_code': '',
            'email': '',
            'rating': '5',
            'title': 'Nice',
            'content': 'Good mod'
        })
        self.assertEqual(resp_fail.status_code, 302)
        self.assertFalse(Review.objects.filter(product=self.product).exists())

        # 2. Guest with non-existent order fails
        resp_invalid_order = self.client.post(review_url, {
            'order_code': 'PM-FAKE99999',
            'email': 'fake@example.com',
            'rating': '5',
            'title': 'Nice',
            'content': 'Good mod'
        })
        self.assertEqual(resp_invalid_order.status_code, 302)
        self.assertFalse(Review.objects.filter(product=self.product).exists())

        # 3. Create completed order with this product
        order = Order.objects.create(
            code='PM-VALID1234',
            full_name='John Guest',
            email='guest@example.com',
            billing_address='123 Test St',
            total_amount=10.00,
            status='completed',
            payment_status='Success'
        )
        OrderItem.objects.create(order=order, product=self.product, price=10.00)

        # 4. Valid guest review succeeds
        resp_valid = self.client.post(review_url, {
            'order_code': 'PM-VALID1234',
            'email': 'guest@example.com',
            'rating': '5',
            'title': 'Excellent Work',
            'content': 'Runs smoothly without any crashes.'
        })
        self.assertEqual(resp_valid.status_code, 302)
        review = Review.objects.filter(product=self.product, order=order).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.reviewer_name, 'John Guest')
        self.assertEqual(review.rating, 5)

        # 5. Duplicate review for same order is rejected
        resp_dup = self.client.post(review_url, {
            'order_code': 'PM-VALID1234',
            'email': 'guest@example.com',
            'rating': '4',
            'title': 'Another review',
            'content': 'Trying to post again.'
        })
        self.assertEqual(resp_dup.status_code, 302)
        self.assertEqual(Review.objects.filter(product=self.product, order=order).count(), 1)

    def test_product_tabs_content_and_empty_states(self):
        """FIX 5: Verify all 4 tabs display their content or graceful empty states."""
        self.product.stock_status = 'available'
        self.product.save()

        detail_url = reverse('marketplace:product_detail', args=[self.product.slug])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        # Test tab buttons exist
        self.assertContains(response, 'data-tab="tabAbout"')
        self.assertContains(response, 'data-tab="tabRequirements"')
        self.assertContains(response, 'data-tab="tabInstall"')
        self.assertContains(response, 'data-tab="tabChangelog"')

        # Test populated fields
        self.assertContains(response, "Long description details")
        self.assertContains(response, "ScriptHookV")
        self.assertContains(response, "Copy and paste files")

        # Test empty version history renders graceful empty state
        self.assertContains(response, "No version history available.")

    def test_product_detail_actions_no_paypal_direct_button(self):
        """Verify product detail page shows only Add to Cart and Buy Now, and no direct PayPal button."""
        self.product.stock_status = 'available'
        self.product.save()

        detail_url = reverse('marketplace:product_detail', args=[self.product.slug])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        # 1. Must contain Add to Cart and Buy Now buttons
        self.assertContains(response, "Add to Cart")
        self.assertContains(response, "Buy Now")
        self.assertContains(response, 'id="ajaxAddToCartBtn"')

        # 2. Must NOT contain direct PayPal button or form
        self.assertNotContains(response, "btn-paypal-express")
        self.assertNotContains(response, "PayPal Express Checkout Direct")

        # 3. Test centralized checkout flow:
        # Step A: Buy Now triggers cart_add
        cart_add_url = reverse('orders:cart_add', args=[self.product.id])
        resp_buy = self.client.post(cart_add_url, {'checkout_direct': 'true'})
        self.assertEqual(resp_buy.status_code, 302)
        self.assertRedirects(resp_buy, reverse('orders:cart'))

        # Step B: Cart detail page displays items
        resp_cart = self.client.get(reverse('orders:cart'))
        self.assertEqual(resp_cart.status_code, 200)
        self.assertContains(resp_cart, self.product.name)

        # Step C: Proceed to checkout
        resp_checkout_page = self.client.get(reverse('orders:checkout'))
        self.assertEqual(resp_checkout_page.status_code, 200)
        self.assertContains(resp_checkout_page, "Checkout")
