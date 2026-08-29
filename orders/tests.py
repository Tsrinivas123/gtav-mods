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
