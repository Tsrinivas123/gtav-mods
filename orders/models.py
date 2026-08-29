from django.db import models
from django.contrib.auth.models import User
from marketplace.models import Product
import uuid


class Coupon(models.Model):
    DISCOUNT_CHOICES = (
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount ($)'),
    )
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    active = models.BooleanField(default=True)
    expiration_date = models.DateField()

    def __str__(self):
        return f"{self.code} - {self.discount_value} ({self.discount_type})"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    code = models.CharField(max_length=100, unique=True, blank=True)
    invoice_number = models.CharField(max_length=30, blank=True, null=True, unique=True)

    # Billing
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    billing_address = models.TextField()

    # Amounts
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Order state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Payment details (recorded only after server-side verification)
    payment_method = models.CharField(max_length=50, default='Razorpay')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_id = models.CharField(max_length=200, blank=True, null=True)
    payment_gateway = models.CharField(max_length=50, blank=True, null=True)
    payment_transaction_time = models.DateTimeField(null=True, blank=True)
    payment_gateway_response = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"PM-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.code} by {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} inside {self.order.code}"

