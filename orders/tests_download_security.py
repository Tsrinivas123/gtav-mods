import os
from unittest.mock import patch
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from marketplace.models import Product, Category, VersionHistory
from orders.models import Order, OrderItem
from django.conf import settings


class DownloadSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Supercars", slug="supercars", status="active")
        
        # Product 1: Paid product (Terzo)
        self.product_terzo = Product.objects.create(
            name="Lamborghini Terzo Millennio",
            slug="terzo",
            category=self.category,
            price=Decimal("500.00"),
            stock_status="available",
            downloads_count=0
        )
        self.version_terzo = VersionHistory.objects.create(
            product=self.product_terzo,
            version="1.0.0",
            download_file="products/files/terzo_v100.zip"
        )

        # Product 2: Paid product (Centenario)
        self.product_centenario = Product.objects.create(
            name="Lamborghini Centenario",
            slug="centenario",
            category=self.category,
            price=Decimal("400.00"),
            stock_status="available",
            downloads_count=0
        )
        self.version_centenario = VersionHistory.objects.create(
            product=self.product_centenario,
            version="1.0.0",
            download_file="products/files/centenario_v100.zip"
        )

        # Product 3: Free product
        self.product_free = Product.objects.create(
            name="Free Drift Handling",
            slug="free-drift",
            category=self.category,
            price=Decimal("0.00"),
            stock_status="available",
            downloads_count=0
        )
        self.version_free = VersionHistory.objects.create(
            product=self.product_free,
            version="1.0.0",
            download_file="products/files/free_drift.zip"
        )

        # Test User
        self.user = User.objects.create_user(username="testbuyer", email="buyer@test.com", password="password123")

    # 1. Unpaid visitor -> download denied (403)
    def test_unpaid_visitor_download_denied(self):
        url = reverse("orders:download_file", args=[self.version_terzo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    # 2. Direct download URL without a verified order -> denied (403)
    def test_direct_download_url_without_verified_order(self):
        self.client.login(username="testbuyer", password="password123")
        url = reverse("orders:download_file", args=[self.version_terzo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    # 3. Failed or pending payment -> denied (403)
    def test_pending_payment_denied(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Test Buyer",
            email="buyer@test.com",
            billing_address="123 Test St",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        # User logged in with pending order
        self.client.login(username="testbuyer", password="password123")
        url = reverse("orders:download_file", args=[self.version_terzo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_failed_payment_denied(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Test Buyer",
            email="buyer@test.com",
            billing_address="123 Test St",
            total_amount=Decimal("500.00"),
            payment_status="Failed",
            status="pending"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        self.client.login(username="testbuyer", password="password123")
        url = reverse("orders:download_file", args=[self.version_terzo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    # 4. Verified paid order for the correct product -> download allowed
    @patch("core.supabase_storage.is_configured", return_value=True)
    @patch("core.supabase_storage.create_signed_url", return_value="https://supabase.co/storage/v1/object/sign/pawanmod-files/products/files/terzo_v100.zip?token=xyz123")
    def test_verified_paid_order_for_correct_product_allowed(self, mock_signed, mock_is_conf):
        order = Order.objects.create(
            user=self.user,
            full_name="Test Buyer",
            email="buyer@test.com",
            billing_address="123 Test St",
            total_amount=Decimal("500.00"),
            payment_status="Success",
            status="completed"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        self.client.login(username="testbuyer", password="password123")
        url = reverse("orders:download_file", args=[self.version_terzo.id])
        response = self.client.get(url)

        # Must redirect to the signed URL (never a public permanent url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://supabase.co/storage/v1/object/sign/", response.url)
        self.assertIn("token=xyz123", response.url)

        # Downloads count incremented
        self.product_terzo.refresh_from_db()
        self.assertEqual(self.product_terzo.downloads_count, 1)

    # Guest checkout with session purchased_orders
    @patch("core.supabase_storage.is_configured", return_value=True)
    @patch("core.supabase_storage.create_signed_url", return_value="https://supabase.co/signed/guest.zip")
    def test_guest_verified_order_allowed(self, mock_signed, mock_is_conf):
        order = Order.objects.create(
            full_name="Guest Buyer",
            email="guest@test.com",
            billing_address="Guest Address",
            total_amount=Decimal("500.00"),
            payment_status="Success",
            status="completed"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        session = self.client.session
        session["purchased_orders"] = [order.code]
        session.save()

        url = reverse("orders:download_file", args=[self.version_terzo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://supabase.co/signed/guest.zip")

    # 5. Paid order for a different product -> denied (403)
    def test_paid_order_for_different_product_denied(self):
        # Buyer bought Centenario (Product 2), but NOT Terzo (Product 1)
        order = Order.objects.create(
            user=self.user,
            full_name="Test Buyer",
            email="buyer@test.com",
            billing_address="123 Test St",
            total_amount=Decimal("400.00"),
            payment_status="Success",
            status="completed"
        )
        OrderItem.objects.create(order=order, product=self.product_centenario, price=Decimal("400.00"))

        self.client.login(username="testbuyer", password="password123")
        # Attempt to download Terzo
        url = reverse("orders:download_file", args=[self.version_terzo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    # 6. Product detail page checks
    def test_product_detail_page_unpaid_visitor(self):
        response = self.client.get(reverse("marketplace:product_detail", args=["terzo"]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        
        # Must show Buy Now and Add to Cart
        self.assertIn("Buy Now", content)
        self.assertIn("Add to Cart", content)
        
        # Must NOT show working download button for unpaid visitor
        self.assertNotIn(reverse("orders:download_file", args=[self.version_terzo.id]), content)
        # Must show locked text in version history
        self.assertIn("Purchase this mod to download", content)

    def test_product_detail_page_verified_purchaser(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Test Buyer",
            email="buyer@test.com",
            billing_address="123 Test St",
            total_amount=Decimal("500.00"),
            payment_status="Success",
            status="completed"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        self.client.login(username="testbuyer", password="password123")
        response = self.client.get(reverse("marketplace:product_detail", args=["terzo"]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Must show download link and Purchased badge
        self.assertIn(reverse("orders:download_file", args=[self.version_terzo.id]), content)
        self.assertIn("Purchased", content)

    # 7. Direct media serve access blocked for archives
    def test_direct_media_serve_archive_denied(self):
        response = self.client.get("/media/products/files/terzo_v100.zip")
        self.assertEqual(response.status_code, 404)

        response_rar = self.client.get("/media/products/files/test.rar")
        self.assertEqual(response_rar.status_code, 404)

        response_7z = self.client.get("/media/uploads/archive.7z")
        self.assertEqual(response_7z.status_code, 404)

    # 8. Free product download allowed without order
    @patch("core.supabase_storage.is_configured", return_value=True)
    @patch("core.supabase_storage.create_signed_url", return_value="https://supabase.co/signed/free.zip")
    def test_free_product_download_allowed(self, mock_signed, mock_is_conf):
        url = reverse("orders:download_file", args=[self.version_free.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://supabase.co/signed/free.zip")

    # 9. Payment verification fails closed when Razorpay keys missing
    def test_payment_complete_fails_closed_when_keys_missing(self):
        order = Order.objects.create(
            full_name="Buyer",
            email="buyer@test.com",
            billing_address="Address",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending"
        )
        with patch.object(settings, "RAZORPAY_KEY_ID", ""), patch.object(settings, "RAZORPAY_KEY_SECRET", ""):
            response = self.client.post(
                reverse("orders:payment_complete"),
                data='{"order_code": "' + order.code + '", "payment_id": "pay_123", "gateway": "Razorpay"}',
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 503)
            order.refresh_from_db()
            self.assertEqual(order.payment_status, "Failed")
            self.assertNotEqual(order.status, "completed")

    # 10. Manual UPI saves as pending and does not unlock download
    def test_manual_upi_payment_saves_pending_and_denies_download(self):
        order = Order.objects.create(
            full_name="UPI Buyer",
            email="upi@test.com",
            billing_address="UPI Address",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        response = self.client.post(
            reverse("orders:payment_complete"),
            data='{"order_code": "' + order.code + '", "payment_id": "upi_ref_9999", "gateway": "UPI"}',
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "pending")

        order.refresh_from_db()
        self.assertEqual(order.payment_status, "Pending")
        self.assertEqual(order.status, "pending")

        # Session does not have purchased_orders
        self.assertNotIn(order.code, self.client.session.get("purchased_orders", []))

        # Download attempt must be forbidden (403)
        dl_url = reverse("orders:download_file", args=[self.version_terzo.id])
        dl_response = self.client.get(dl_url)
        self.assertEqual(dl_response.status_code, 403)

    # 11. Razorpay backend order initialization with exact database price
    @patch("razorpay.Client")
    def test_razorpay_backend_order_initialization(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.order.create.return_value = {"id": "order_test_rzp_999"}

        order = Order.objects.create(
            user=self.user,
            full_name="Razorpay Buyer",
            email="rzpbuyer@test.com",
            billing_address="Test Address",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending",
            payment_method="Razorpay"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        with patch.object(settings, "RAZORPAY_KEY_ID", "rzp_test_123456"), \
             patch.object(settings, "RAZORPAY_KEY_SECRET", "test_secret_999"):
            response = self.client.get(reverse("orders:payment_gate", args=[order.code]))
            self.assertEqual(response.status_code, 200)

            # Check that client.order.create was called with exact amount in paise (50000)
            mock_client.order.create.assert_called_once_with({
                "amount": 50000,
                "currency": "INR",
                "receipt": order.code
            })

            # Check context parameters
            self.assertTrue(response.context["is_test_mode"])
            self.assertEqual(response.context["razorpay_order_id"], "order_test_rzp_999")

            order.refresh_from_db()
            self.assertIn("order_test_rzp_999", order.payment_gateway_response)

    # 12. Razorpay verified signature unlocks mod download
    @patch("core.supabase_storage.is_configured", return_value=True)
    @patch("core.supabase_storage.create_signed_url", return_value="https://supabase.co/signed/terzo_v100.zip")
    @patch("razorpay.Client")
    def test_razorpay_successful_signature_verification_unlocks_download(self, mock_client_cls, mock_signed, mock_is_conf):
        mock_client = mock_client_cls.return_value
        # verify_payment_signature does not raise when valid
        mock_client.utility.verify_payment_signature.return_value = True

        order = Order.objects.create(
            user=self.user,
            full_name="Razorpay Buyer",
            email="rzpbuyer@test.com",
            billing_address="Test Address",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending",
            payment_method="Razorpay",
            payment_gateway_response='{"razorpay_order_id": "order_test_rzp_111"}'
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        self.client.login(username="testbuyer", password="password123")

        with patch.object(settings, "RAZORPAY_KEY_ID", "rzp_test_123456"), \
             patch.object(settings, "RAZORPAY_KEY_SECRET", "test_secret_999"):
            payload = {
                "order_code": order.code,
                "payment_id": "pay_test_987654",
                "razorpay_order_id": "order_test_rzp_111",
                "razorpay_signature": "valid_hmac_sha256_sig",
                "gateway": "Razorpay"
            }
            res = self.client.post(
                reverse("orders:payment_complete"),
                data=payload,
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["status"], "success")

            order.refresh_from_db()
            self.assertEqual(order.payment_status, "Success")
            self.assertEqual(order.status, "completed")
            self.assertEqual(order.payment_id, "pay_test_987654")

            # Download is now unlocked!
            dl_url = reverse("orders:download_file", args=[self.version_terzo.id])
            dl_res = self.client.get(dl_url)
            self.assertEqual(dl_res.status_code, 302)
            self.assertEqual(dl_res.url, "https://supabase.co/signed/terzo_v100.zip")

    # 13. Razorpay tampered/invalid signature fails and keeps download locked
    @patch("razorpay.Client")
    def test_razorpay_invalid_signature_denies_download(self, mock_client_cls):
        import razorpay.errors
        mock_client = mock_client_cls.return_value
        mock_client.utility.verify_payment_signature.side_effect = razorpay.errors.SignatureVerificationError("Signature mismatch")

        order = Order.objects.create(
            user=self.user,
            full_name="Razorpay Buyer",
            email="rzpbuyer@test.com",
            billing_address="Test Address",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending",
            payment_method="Razorpay",
            payment_gateway_response='{"razorpay_order_id": "order_test_rzp_111"}'
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        self.client.login(username="testbuyer", password="password123")

        with patch.object(settings, "RAZORPAY_KEY_ID", "rzp_test_123456"), \
             patch.object(settings, "RAZORPAY_KEY_SECRET", "test_secret_999"):
            payload = {
                "order_code": order.code,
                "payment_id": "pay_test_987654",
                "razorpay_order_id": "order_test_rzp_111",
                "razorpay_signature": "tampered_fake_signature",
                "gateway": "Razorpay"
            }
            res = self.client.post(
                reverse("orders:payment_complete"),
                data=payload,
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["status"], "failed")

            order.refresh_from_db()
            self.assertEqual(order.payment_status, "Failed")
            self.assertNotEqual(order.status, "completed")

            # Download attempt must be rejected (403)
            dl_url = reverse("orders:download_file", args=[self.version_terzo.id])
            dl_res = self.client.get(dl_url)
            self.assertEqual(dl_res.status_code, 403)

    # 14. Razorpay order ID mismatch rejected
    @patch("razorpay.Client")
    def test_razorpay_order_id_mismatch_rejected(self, mock_client_cls):
        order = Order.objects.create(
            user=self.user,
            full_name="Razorpay Buyer",
            email="rzpbuyer@test.com",
            billing_address="Test Address",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending",
            payment_method="Razorpay",
            payment_gateway_response='{"razorpay_order_id": "order_real_123"}'
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        with patch.object(settings, "RAZORPAY_KEY_ID", "rzp_test_123456"), \
             patch.object(settings, "RAZORPAY_KEY_SECRET", "test_secret_999"):
            payload = {
                "order_code": order.code,
                "payment_id": "pay_test_987654",
                "razorpay_order_id": "order_stolen_from_other_account",
                "razorpay_signature": "signature_123",
                "gateway": "Razorpay"
            }
            res = self.client.post(
                reverse("orders:payment_complete"),
                data=payload,
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["status"], "failed")
            self.assertIn("mismatch", res.json()["message"])

    # 15. Razorpay payment cancellation marks order Cancelled and denies download
    def test_razorpay_cancellation_denies_download(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Razorpay Buyer",
            email="rzpbuyer@test.com",
            billing_address="Test Address",
            total_amount=Decimal("500.00"),
            payment_status="Pending",
            status="pending",
            payment_method="Razorpay"
        )
        OrderItem.objects.create(order=order, product=self.product_terzo, price=Decimal("500.00"))

        self.client.login(username="testbuyer", password="password123")

        res = self.client.post(
            reverse("orders:payment_complete"),
            data={"order_code": order.code, "action": "cancel", "response": "User dismissed popup"},
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "cancelled")

        order.refresh_from_db()
        self.assertEqual(order.payment_status, "Cancelled")
        self.assertEqual(order.status, "cancelled")

        dl_url = reverse("orders:download_file", args=[self.version_terzo.id])
        dl_res = self.client.get(dl_url)
        self.assertEqual(dl_res.status_code, 403)

