from django.test import TestCase
from django.utils import timezone
from .models import Coupon, Order
import datetime

class OrderModelTests(TestCase):
    def setUp(self):
        self.coupon = Coupon.objects.create(
            code="SAVE50",
            discount_type="percentage",
            discount_value=50.00,
            expiration_date=timezone.now().date() + datetime.timedelta(days=10)
        )
        self.order = Order.objects.create(
            full_name="Alex Mercer",
            email="alex@prototype.com",
            billing_address="123 Gentek Tower, Manhattan",
            total_amount=50.00,
            coupon=self.coupon,
            discount_amount=50.00,
            payment_method="PayPal",
            payment_status="Completed"
        )

    def test_order_code_auto_generation(self):
        """Verify unique Order track codes generate automatically."""
        self.assertTrue(self.order.code.startswith("PM-"))

    def test_coupon_expiration_check(self):
        """Verify coupon expiration checker aligns with future date intervals."""
        self.assertGreaterEqual(self.coupon.expiration_date, timezone.now().date())


class CartViewTests(TestCase):
    def setUp(self):
        from marketplace.models import Category, Product
        from decimal import Decimal
        self.category = Category.objects.create(name="Vehicles", slug="vehicles")
        self.product = Product.objects.create(
            name="Test Cart Supercar",
            slug="test-cart-supercar",
            category=self.category,
            price=Decimal("150.00"),
            short_description="Test short",
            description="Test desc",
            requirements="None",
            installation_guide="None"
        )

    def test_cart_page_renders_proceed_to_checkout_and_no_paypal(self):
        """Verify that when products are in the cart, Proceed to Checkout is present and Pay with PayPal is absent."""
        from django.urls import reverse
        # Add item to cart
        self.client.post(reverse('orders:cart_add', args=[self.product.id]))

        # Load cart page
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 200)

        # Confirm Proceed to Checkout button exists
        self.assertContains(response, "Proceed to Checkout")
        self.assertContains(response, reverse('orders:checkout'))

        # Confirm PayPal button and form are NOT present
        self.assertNotContains(response, "Pay with PayPal")
        self.assertNotContains(response, "PAY WITH PAYPAL")
        self.assertNotContains(response, "paypalCartForm")
        self.assertNotContains(response, "btn-cart-paypal")

    def test_cart_page_empty_no_paypal(self):
        """Verify that empty cart page does not contain any PayPal buttons."""
        from django.urls import reverse
        response = self.client.get(reverse('orders:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Cart is Empty")
        self.assertNotContains(response, "Pay with PayPal")
        self.assertNotContains(response, "PAY WITH PAYPAL")
