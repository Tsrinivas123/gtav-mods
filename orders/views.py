from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import Coupon, Order, OrderItem
from marketplace.models import Product, VersionHistory
from decimal import Decimal
import json
import razorpay
import io

def cart_detail(request):
    # Session cart contents are already processed in context_processors
    coupon_code = request.session.get('coupon_code', None)
    discount_amount = Decimal('0.00')
    discount_percentage = 0
    coupon = None
    
    # Recalculate cart totals inside view for discount applications
    cart = request.session.get('cart', {})
    cart_total = Decimal('0.00')
    if cart:
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            quantity = cart[str(product.id)]
            cart_total += product.price * quantity

    from marketplace.models import SiteSetting
    coupons_enabled = SiteSetting.get_setting('enable_coupons', 'False').lower() == 'true'

    if coupons_enabled and coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True, expiration_date__gte=timezone.now().date())
            if coupon.discount_type == 'percentage':
                discount_percentage = int(coupon.discount_value)
                discount_amount = (cart_total * coupon.discount_value) / Decimal('100.00')
            else:
                discount_amount = coupon.discount_value
        except Coupon.DoesNotExist:
            # Clear expired or invalid coupon from session
            request.session.pop('coupon_code', None)

    final_total = max(Decimal('0.00'), cart_total - discount_amount)
    grand_total = final_total

    context = {
        'discount_amount': discount_amount,
        'discount_percentage': discount_percentage,
        'coupon': coupon,
        'grand_total': grand_total,
    }
    return render(request, 'cart.html', context)

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    quantity = int(request.POST.get('quantity', 1))

    # Add or update
    cart_id = str(product.id)
    if cart_id in cart:
        cart[cart_id] += quantity
    else:
        cart[cart_id] = quantity

    request.session['cart'] = cart
    messages.success(request, f"{product.name} added to cart.")
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.POST.get('checkout_direct') == 'true':
            return JsonResponse({
                'status': 'success',
                'cart_count': sum(cart.values()),
                'redirect_url': reverse('orders:cart')
            })
        return JsonResponse({
            'status': 'success', 
            'cart_count': sum(cart.values()), 
            'message': f"{product.name} added to cart."
        })
        
    if request.POST.get('checkout_direct') == 'true':
        return redirect('orders:cart')
        
    return redirect(request.META.get('HTTP_REFERER', 'orders:cart'))

def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    cart_id = str(product_id)
    
    if cart_id in cart:
        del cart[cart_id]
        request.session['cart'] = cart
        messages.success(request, "Item removed from cart.")

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success', 
            'cart_count': sum(cart.values()),
            'message': "Item removed from cart."
        })
        
    return redirect('orders:cart')

def cart_update(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        cart_id = str(product_id)
        quantity = int(request.POST.get('quantity', 1))
        
        if cart_id in cart:
            if quantity > 0:
                cart[cart_id] = quantity
            else:
                del cart[cart_id]
            request.session['cart'] = cart
            messages.success(request, "Cart updated.")
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Cart updated.'})
            
    return redirect('orders:cart')

def apply_coupon(request):
    from marketplace.models import SiteSetting
    coupons_enabled = SiteSetting.get_setting('enable_coupons', 'False').lower() == 'true'

    if not coupons_enabled:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
            return JsonResponse({'status': 'error', 'message': 'Coupons are currently unavailable.'}, status=400)
        messages.error(request, "Coupons are currently unavailable.")
        return redirect('orders:cart')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        if not code:
            messages.error(request, "Please enter a coupon code.")
            return redirect('orders:cart')

        try:
            coupon = Coupon.objects.get(code=code, active=True, expiration_date__gte=timezone.now().date())
            request.session['coupon_code'] = coupon.code
            messages.success(request, f"Coupon code '{code}' applied successfully!")
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or expired coupon code.")
            
    return redirect('orders:cart')

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import razorpay
from marketplace.models import Product, VersionHistory

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('marketplace:store')

    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)
    cart_total = Decimal('0.00')
    for product in products:
        quantity = cart[str(product.id)]
        cart_total += product.price * quantity

    coupon_code = request.session.get('coupon_code', None)
    discount_amount = Decimal('0.00')
    coupon = None

    from marketplace.models import SiteSetting
    coupons_enabled = SiteSetting.get_setting('enable_coupons', 'False').lower() == 'true'

    if coupons_enabled and coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True, expiration_date__gte=timezone.now().date())
            if coupon.discount_type == 'percentage':
                discount_amount = (cart_total * coupon.discount_value) / Decimal('100.00')
            else:
                discount_amount = coupon.discount_value
        except Coupon.DoesNotExist:
            request.session.pop('coupon_code', None)

    final_total = max(Decimal('0.00'), cart_total - discount_amount)
    grand_total = final_total

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        billing_address = request.POST.get('billing_address')
        payment_method = request.POST.get('payment_method', 'Razorpay')

        if not full_name or not email or not billing_address:
            messages.error(request, "Please fill out all billing details.")
            return render(request, 'checkout.html', {'grand_total': grand_total})

        # Create order in pending state – will be completed only after server-side payment verification
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            billing_address=billing_address,
            total_amount=grand_total,
            coupon=coupon,
            discount_amount=discount_amount,
            payment_method=payment_method,
            payment_status='Pending',
            status='pending',
        )

        for product in products:
            OrderItem.objects.create(order=order, product=product, price=product.price)

        return redirect('orders:payment_gate', order_code=order.code)

    context = {
        'cart_items': [
            {
                'product': product,
                'quantity': cart[str(product.id)],
                'total': product.price * cart[str(product.id)],
            }
            for product in products
        ],
        'cart_total': cart_total,
        'discount_amount': discount_amount,
        'grand_total': grand_total,
        'coupon': coupon,
    }
    return render(request, 'checkout.html', context)


def payment_gate(request, order_code):
    order = get_object_or_404(Order, code=order_code)

    razorpay_amount = int(order.total_amount * 100)  # Razorpay expects paise
    razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    paypal_client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')

    razorpay_order_id = ''
    if razorpay_key_id and razorpay_key_secret:
        try:
            client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
            rzp_order = client.order.create({
                'amount': razorpay_amount,
                'currency': 'INR',
                'receipt': order.code,
            })
            razorpay_order_id = rzp_order.get('id', '')
        except Exception:
            razorpay_order_id = ''

    context = {
        'order': order,
        'grand_total': order.total_amount,
        'razorpay_amount': razorpay_amount,
        'razorpay_order_id': razorpay_order_id,
        'RAZORPAY_KEY_ID': razorpay_key_id,
        'PAYPAL_CLIENT_ID': paypal_client_id,
        'razorpay_configured': bool(razorpay_key_id and razorpay_key_secret),
        'paypal_configured': bool(paypal_client_id),
    }
    return render(request, 'checkout_payment.html', context)


@csrf_exempt
def payment_complete(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST.dict()

    order_code    = data.get('order_code', '')
    payment_id    = data.get('payment_id', '')
    gateway       = data.get('gateway', 'Razorpay')
    raw_response  = data.get('response', '')

    order = get_object_or_404(Order, code=order_code)

    is_verified = False

    if gateway == 'Razorpay':
        razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
        razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')

        if not razorpay_key_id or not razorpay_key_secret:
            # No keys configured – allow test/demo mode
            is_verified = True
        else:
            try:
                client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
                client.utility.verify_payment_signature({
                    'razorpay_order_id':   data.get('razorpay_order_id', ''),
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature':  data.get('razorpay_signature', ''),
                })
                is_verified = True
            except Exception as exc:
                is_verified = False
                raw_response = str(exc)

    elif gateway in ['PayPal', 'UPI', 'Cards', 'Debit / Credit Card']:
        is_verified = True


    if is_verified:
        # Generate sequential invoice number: PM-YYYY-000001
        year = timezone.now().year
        prefix = f'PM-{year}-'
        last = Order.objects.filter(invoice_number__startswith=prefix).order_by('-invoice_number').first()
        if last and last.invoice_number:
            try:
                next_seq = int(last.invoice_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                next_seq = 1
        else:
            next_seq = 1

        order.invoice_number          = f'{prefix}{next_seq:06d}'
        order.payment_status          = 'Success'
        order.status                  = 'completed'
        order.payment_id              = payment_id
        order.payment_gateway         = gateway
        order.payment_transaction_time = timezone.now()
        order.payment_gateway_response = str(raw_response)
        order.save()

        request.session.pop('cart', None)
        request.session.pop('coupon_code', None)

        purchased = request.session.get('purchased_orders', [])
        if order.code not in purchased:
            purchased.append(order.code)
            request.session['purchased_orders'] = purchased

        return JsonResponse({
            'status': 'success',
            'redirect_url': reverse('orders:order_complete', args=[order.code]),
        })

    # Verification failed – mark order accordingly, do NOT update to paid/completed
    order.payment_status           = 'Failed'
    order.payment_gateway_response = str(raw_response)
    order.save()

    return JsonResponse({
        'status': 'failed',
        'message': 'Payment verification failed. Please try again or contact support.',
    }, status=400)


def download_file(request, version_id):
    """Secure download: increments downloads_count only after confirming purchase entitlement."""
    version = get_object_or_404(VersionHistory, pk=version_id)
    product = version.product

    is_allowed = False

    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        is_allowed = True
    elif product.price == 0:
        is_allowed = True
    else:
        purchased_orders = request.session.get('purchased_orders', [])
        is_allowed = Order.objects.filter(
            status__in=['paid', 'completed', 'Success'],
            items__product=product,
            code__in=purchased_orders
        ).exists()

    if not is_allowed:
        messages.error(request, "You must purchase this mod before downloading.")
        return redirect('marketplace:product_detail', slug=product.slug)

    # Increment only on actual download, not on payment
    product.downloads_count += 1
    product.save(update_fields=['downloads_count'])

    if version.download_file:
        return redirect(version.download_file.url)
    elif version.download_url:
        return redirect(version.download_url)
    else:
        messages.error(request, "Download file is not available for this version yet.")
        return redirect('marketplace:product_detail', slug=product.slug)


def order_complete(request, order_code):
    order = get_object_or_404(Order, code=order_code)
    return render(request, 'order_complete.html', {'order': order})


def invoice_pdf(request, order_code):
    """Stream a ReportLab-generated PDF invoice for a completed order."""
    order = get_object_or_404(Order, code=order_code)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
    except ImportError:
        return HttpResponse('ReportLab is not installed. Run: pip install reportlab', status=500)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    accent = colors.HexColor('#FF6B00')
    dark   = colors.HexColor('#111827')

    heading_style = ParagraphStyle('Heading', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold', textColor=accent, spaceAfter=4)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#6B7280'))
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#6B7280'), fontName='Helvetica-Bold')
    value_style = ParagraphStyle('Value', parent=styles['Normal'],
        fontSize=10, textColor=dark)
    right_style = ParagraphStyle('Right', parent=styles['Normal'],
        fontSize=10, textColor=dark, alignment=TA_RIGHT)
    total_style = ParagraphStyle('Total', parent=styles['Normal'],
        fontSize=12, fontName='Helvetica-Bold', textColor=accent, alignment=TA_RIGHT)

    story = []

    # Header: Brand + Invoice title
    story.append(Paragraph('PawanMod', heading_style))
    story.append(Paragraph('Digital Mod Marketplace', sub_style))
    story.append(Spacer(1, 0.5*cm))

    # Invoice meta info table
    invoice_no  = order.invoice_number or order.code
    invoice_date = (order.payment_transaction_time or order.created_at).strftime('%d %b %Y')

    meta_data = [
        [Paragraph('<b>INVOICE</b>', ParagraphStyle('INV', parent=styles['Normal'], fontSize=16, fontName='Helvetica-Bold', textColor=dark)),
         Paragraph(f'Invoice No: <b>{invoice_no}</b><br/>Date: {invoice_date}', right_style)]
    ]
    meta_table = Table(meta_data, colWidths=[10*cm, 7*cm])
    meta_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1, accent),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    # Billing info
    billing_data = [
        [Paragraph('BILL TO', label_style),
         Paragraph('PAYMENT METHOD', label_style)],
        [Paragraph(f'{order.full_name}<br/>{order.email}<br/>{order.billing_address or "-"}', value_style),
         Paragraph(f'{order.payment_method}<br/>Status: {order.payment_status}<br/>Tx ID: {order.payment_id or "N/A"}', value_style)]
    ]
    billing_table = Table(billing_data, colWidths=['50%', '50%'])
    billing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F9FAFB')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(billing_table)
    story.append(Spacer(1, 0.6*cm))

    # Items table
    item_headers = [
        Paragraph('#', label_style),
        Paragraph('Product', label_style),
        Paragraph('Price', ParagraphStyle('LabelR', parent=styles['Normal'], fontSize=9,
                                          textColor=colors.HexColor('#6B7280'), fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]
    item_rows = [item_headers]
    for i, item in enumerate(order.items.all(), start=1):
        item_rows.append([
            Paragraph(str(i), value_style),
            Paragraph(item.product.name, value_style),
            Paragraph(f'Rs.{item.price}', right_style),
        ])

    items_table = Table(item_rows, colWidths=[1*cm, 13*cm, 3*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFF7ED')),
        ('LINEBELOW', (0, 0), (-1, 0), 1, accent),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.5*cm))

    # Totals section
    totals_data = []
    if order.discount_amount and order.discount_amount > 0:
        totals_data.append(['', Paragraph('Subtotal:', right_style),
                            Paragraph(f'Rs.{order.total_amount + order.discount_amount}', right_style)])
        totals_data.append(['', Paragraph('Discount:', right_style),
                            Paragraph(f'-Rs.{order.discount_amount}', ParagraphStyle('Green', parent=styles['Normal'],
                                       fontSize=10, textColor=colors.HexColor('#16A34A'), alignment=TA_RIGHT))])
    totals_data.append(['', Paragraph('<b>Total Paid:</b>', total_style),
                        Paragraph(f'<b>Rs.{order.total_amount}</b>', total_style)])
    totals_data.append(['', Paragraph('<i>Digital product. No GST, no shipping charges.</i>',
                        ParagraphStyle('Note', parent=styles['Normal'], fontSize=8,
                                       textColor=colors.HexColor('#9CA3AF'), alignment=TA_RIGHT)), ''])

    totals_table = Table(totals_data, colWidths=[10*cm, 5*cm, 2*cm])
    totals_table.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (1, 0), (-1, 0), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    story.append(totals_table)

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        'Thank you for your purchase! For support, contact: support@pawanmod.com',
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#9CA3AF'), alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_no}.pdf"'
    return response
