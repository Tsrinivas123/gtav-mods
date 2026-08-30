from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Avg, Sum, Count
from django.http import JsonResponse
from .models import Product, Category, Review, ProductImage, VersionHistory, ContactMessage, ContactReply
from blog.models import BlogPost
from orders.models import Order, OrderItem
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import json
import os
import datetime


def home(request):
    featured_categories = Category.objects.filter(status='active').annotate(
        product_count=Count(
            'products',
            filter=Q(products__stock_status='available', products__is_deleted=False)
        )
    )[:8]
    
    trending_mods = Product.objects.select_related('category').filter(
        category__status='active', is_trending=True, stock_status='available'
    ).order_by('-created_at')[:8]
    
    best_selling_mods = Product.objects.select_related('category').filter(
        category__status='active', stock_status='available'
    ).order_by('-downloads_count')[:8]
    
    top_rated_mods = Product.objects.select_related('category').filter(
        category__status='active', stock_status='available'
    ).annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating')[:8]
    
    featured_mods = Product.objects.select_related('category').filter(
        category__status='active', is_featured=True, stock_status='available'
    ).order_by('-created_at')[:8]
    
    latest_products = Product.objects.select_related('category').filter(
        category__status='active', stock_status='available'
    ).order_by('-created_at')[:8]
    
    from django.utils import timezone
    latest_articles = BlogPost.objects.filter(status='published', publish_date__lte=timezone.now()).order_by('-publish_date')[:3]
    
    context = {
        'featured_categories': featured_categories,
        'trending_mods': trending_mods,
        'best_selling_mods': best_selling_mods,
        'top_rated_mods': top_rated_mods,
        'featured_mods': featured_mods,
        'latest_products': latest_products,
        'latest_articles': latest_articles,
    }
    return render(request, 'home.html', context)

def categories_list(request):
    categories = Category.objects.filter(status='active').annotate(
        product_count=Count(
            'products',
            filter=Q(products__stock_status='available', products__is_deleted=False)
        )
    )
    context = {
        'categories': categories,
    }
    return render(request, 'categories.html', context)

def category_detail(request, slug):
    is_staff = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    if is_staff:
        category = get_object_or_404(Category, slug=slug)
    else:
        category = get_object_or_404(Category, slug=slug, status='active')
        
    manager = Product.all_objects if is_staff else Product.objects
    products_query = manager.select_related('category').filter(category=category)
    if not is_staff:
        products_query = products_query.filter(stock_status='available')
    
    # Apply search text filter
    search_query = request.GET.get('search', '')
    if search_query:
        products_query = products_query.filter(
            Q(name__icontains=search_query) | 
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Apply price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products_query = products_query.filter(price__gte=min_price)
    if max_price:
        products_query = products_query.filter(price__lte=max_price)

    # Apply sorting filter
    sort_by = request.GET.get('sort_by', 'newest')
    if sort_by == 'newest':
        products_query = products_query.order_by('-created_at')
    elif sort_by == 'popular':
        products_query = products_query.order_by('-downloads_count')
    elif sort_by == 'rating':
        products_query = products_query.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'price_low':
        products_query = products_query.order_by('price')
    elif sort_by == 'price_high':
        products_query = products_query.order_by('-price')

    total_count = products_query.count()
    
    context = {
        'category': category,
        'products': products_query,
        'search_query': search_query,
        'min_price': min_price or 0,
        'max_price': max_price or 100,
        'sort_by': sort_by,
        'total_count': total_count,
    }
    return render(request, 'category_detail.html', context)

def membership_info(request):
    return render(request, 'membership.html')

def store(request):
    products_query = Product.objects.select_related('category').filter(stock_status='available', category__status='active')
    categories = Category.objects.filter(status='active')

    # Apply search text filter
    search_query = request.GET.get('search', '')
    if search_query:
        products_query = products_query.filter(
            Q(name__icontains=search_query) | 
            Q(short_description__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Apply category filter
    selected_categories = request.GET.getlist('category')
    if selected_categories:
        products_query = products_query.filter(category__slug__in=selected_categories)

    # Apply price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products_query = products_query.filter(price__gte=min_price)
    if max_price:
        products_query = products_query.filter(price__lte=max_price)

    # Apply sorting filter
    sort_by = request.GET.get('sort_by', 'newest')
    if sort_by == 'newest':
        products_query = products_query.order_by('-created_at')
    elif sort_by == 'popular':
        products_query = products_query.order_by('-downloads_count')
    elif sort_by == 'rating':
        products_query = products_query.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort_by == 'price_low':
        products_query = products_query.order_by('price')
    elif sort_by == 'price_high':
        products_query = products_query.order_by('-price')

    # View Mode Toggle (Grid/List)
    view_mode = request.GET.get('view_mode', 'grid')

    # Pagination calculation
    total_count = products_query.count()
    from django.core.paginator import Paginator
    paginator = Paginator(products_query, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'selected_categories': selected_categories,
        'search_query': search_query,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'sort_by': sort_by,
        'view_mode': view_mode,
        'total_count': total_count,
    }
    return render(request, 'store.html', context)

def product_detail(request, slug):
    from django.db.models import Prefetch
    is_staff = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    manager = Product.all_objects if is_staff else Product.objects
    
    product = get_object_or_404(
        manager.select_related('category')
        .prefetch_related(
            'screenshots',
            'versions',
            Prefetch('reviews', queryset=Review.objects.select_related('user'))
        ),
        slug=slug
    )
    
    if (product.stock_status != 'available' or product.category.status != 'active') and not is_staff:
        from django.http import Http404
        raise Http404("Product is not available.")

    related_products = Product.objects.select_related('category').filter(
        category=product.category, stock_status='available'
    ).exclude(id=product.id)[:4]
    
    # Check if this item is in the user's wishlist
    in_wishlist = False
    has_purchased = False
    if request.user.is_authenticated:
        in_wishlist = request.user.profile.wishlist.filter(id=product.id).exists()
        if request.user.is_staff or request.user.is_superuser:
            has_purchased = True
        else:
            has_purchased = Order.objects.filter(
                user=request.user,
                status__in=['paid', 'completed'],
                items__product=product
            ).exists()

    context = {
        'product': product,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
        'has_purchased': has_purchased,
    }
    return render(request, 'product.html', context)

@login_required
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if not rating or not title or not content:
            messages.error(request, "Please fill out all fields.")
            return redirect('marketplace:product_detail', slug=slug)
            
        Review.objects.create(
            product=product,
            user=request.user,
            rating=int(rating),
            title=title,
            content=content
        )
        messages.success(request, "Review submitted successfully!")
    return redirect('marketplace:product_detail', slug=slug)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def close_inactive_tickets():
    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
    resolved_tickets = ContactMessage.objects.filter(status='resolved')
    
    for ticket in resolved_tickets:
        last_reply = ticket.replies.all().order_by('-created_at').first()
        should_close = False
        
        if last_reply:
            if last_reply.is_admin and last_reply.created_at < thirty_days_ago:
                should_close = True
        else:
            if ticket.created_at < thirty_days_ago:
                should_close = True
                
        if should_close:
            ticket.status = 'closed'
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            auto_close_note = f"\n[Closed Automatically - {timestamp}]"
            if ticket.admin_notes:
                ticket.admin_notes += auto_close_note
            else:
                ticket.admin_notes = auto_close_note
            ticket.save(update_fields=['status', 'admin_notes'])


def contact(request):
    if request.method == 'GET':
        import random
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        request.session['support_captcha_answer'] = num1 + num2
        context = {
            'math_challenge': f"What is {num1} + {num2}?",
            'TURNSTILE_SITE_KEY': os.getenv('TURNSTILE_SITE_KEY', ''),
        }
        return render(request, 'contact.html', context)

    if request.method == 'POST':
        # 1. Rate limiting
        ip = get_client_ip(request)
        one_hour_ago = timezone.now() - datetime.timedelta(hours=1)
        recent_messages_count = ContactMessage.objects.filter(ip_address=ip, created_at__gte=one_hour_ago).count()
        if recent_messages_count >= 5:
            messages.error(request, "Too many support requests submitted. Limit is 5 requests per hour.")
            return redirect('marketplace:contact')

        # 2. Spam verification
        turnstile_site_key = os.getenv('TURNSTILE_SITE_KEY')
        turnstile_secret_key = os.getenv('TURNSTILE_SECRET_KEY')
        
        if turnstile_site_key and turnstile_secret_key:
            import requests
            token = request.POST.get('cf-turnstile-response')
            payload = {
                'secret': turnstile_secret_key,
                'response': token,
                'remoteip': ip
            }
            try:
                res = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', data=payload, timeout=5)
                res_data = res.json()
                if not res_data.get('success', False):
                    messages.error(request, "Spam protection validation failed. Please try again.")
                    return redirect('marketplace:contact')
            except Exception:
                messages.error(request, "Spam protection service unavailable. Please try again later.")
                return redirect('marketplace:contact')
        else:
            captcha_answer = request.POST.get('captcha_answer')
            stored_answer = request.session.get('support_captcha_answer')
            if not captcha_answer or not stored_answer or int(captcha_answer) != int(stored_answer):
                messages.error(request, "Incorrect answer for spam protection. Please try again.")
                return redirect('marketplace:contact')

        if 'support_captcha_answer' in request.session:
            del request.session['support_captcha_answer']

        # 3. Retrieve and sanitize input
        raw_name = request.POST.get('name', '').strip()
        raw_email = request.POST.get('email', '').strip()
        category = request.POST.get('category', '').strip()
        raw_subject = request.POST.get('subject', '').strip()
        raw_message = request.POST.get('message', '').strip()

        name = escape(strip_tags(raw_name))
        email = escape(strip_tags(raw_email))
        subject = escape(strip_tags(raw_subject)) if category == 'other' else ''
        message_text = escape(strip_tags(raw_message))

        if not name or not email or not category or not message_text:
            messages.error(request, "Please fill in all required fields.")
            return redirect('marketplace:contact')

        if category == 'other' and not subject:
            messages.error(request, "Please enter a subject.")
            return redirect('marketplace:contact')

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect('marketplace:contact')

        if len(message_text) < 10:
            messages.error(request, "Message must be at least 10 characters long.")
            return redirect('marketplace:contact')

        # 4. Save to Database
        resolved_subject = dict(ContactMessage.CATEGORY_CHOICES).get(category, category)
        if category == 'other':
            resolved_subject = subject

        ticket = ContactMessage.objects.create(
            full_name=name,
            email=email,
            category=category,
            subject=resolved_subject,
            message=message_text,
            ip_address=ip,
            status='open',
            is_read=False
        )

        # 5. Send emails
        admin_email = 'tusharshrivas7999@gmail.com'
        from_email = settings.DEFAULT_FROM_EMAIL or 'tusharshrivas7999@gmail.com'
        
        from django.urls import reverse
        try:
            admin_path = reverse('admin:marketplace_contactmessage_change', args=[ticket.id])
            admin_url = request.build_absolute_uri(admin_path)
        except Exception:
            admin_url = request.build_absolute_uri(f'/admin/marketplace/contactmessage/{ticket.id}/change/')

        try:
            ticket_url = request.build_absolute_uri(reverse('marketplace:ticket_detail', args=[ticket.ticket_id]))
        except Exception:
            ticket_url = request.build_absolute_uri(f'/tickets/{ticket.ticket_id}/')

        context = {
            'ticket_id': ticket.ticket_id,
            'full_name': ticket.full_name,
            'email': ticket.email,
            'category': ticket.get_category_display(),
            'subject': ticket.subject,
            'message': ticket.message,
            'created_at': ticket.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'admin_url': admin_url,
            'ticket_url': ticket_url,
        }

        # Try rendering and sending HTML email
        try:
            admin_html = render_to_string('emails/support_request_admin.html', context)
            customer_html = render_to_string('emails/customer_autoreply.html', context)
        except Exception:
            # Fallback inline strings if template fails to load/render
            admin_html = f"<html><body><h2>New Support Request {ticket.ticket_id}</h2></body></html>"
            customer_html = f"<html><body><h2>Confirmation for Ticket {ticket.ticket_id}</h2></body></html>"

        admin_text = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "NEW SUPPORT REQUEST\n\n"
            f"Ticket ID: {ticket.ticket_id}\n"
            f"Customer: {ticket.full_name}\n"
            f"Email: {ticket.email}\n"
            f"Category: {ticket.get_category_display()}\n"
            f"Subject: {ticket.subject}\n\n"
            "Message:\n"
            f"{ticket.message}\n\n"
            f"Submitted: {ticket.created_at}\n"
            f"Open Admin: {admin_url}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "This email was automatically generated."
        )

        customer_text = (
            f"Hi {ticket.full_name},\n\n"
            "Thank you for contacting PawanMod.\n"
            "Your support request has been received successfully.\n\n"
            f"Ticket ID: {ticket.ticket_id}\n\n"
            "Our support team usually replies within 24 hours.\n\n"
            "If your issue is related to payment or downloads, please include your Order Number when replying.\n\n"
            "Thank you for choosing PawanMod.\n\n"
            "Regards,\n"
            "PawanMod Support Team\n"
            "https://pawanmod.com"
        )

        email_failed = False

        # Send Admin Notification
        try:
            admin_msg = EmailMultiAlternatives(
                subject=f"📩 New Support Request - {ticket.ticket_id}",
                body=admin_text,
                from_email=from_email,
                to=[admin_email]
            )
            admin_msg.attach_alternative(admin_html, "text/html")
            admin_msg.send(fail_silently=False)
        except Exception:
            email_failed = True

        # Send Customer Auto-Reply
        try:
            customer_msg = EmailMultiAlternatives(
                subject="We received your request - PawanMod",
                body=customer_text,
                from_email=from_email,
                to=[ticket.email]
            )
            customer_msg.attach_alternative(customer_html, "text/html")
            customer_msg.send(fail_silently=False)
        except Exception:
            email_failed = True

        if email_failed:
            messages.success(
                request,
                "Your request has been saved successfully.<br><br>"
                "Email notification could not be delivered, but our support team will still receive it from the dashboard."
            )
        else:
            success_toast = (
                "<strong>✅ Message Sent Successfully!</strong><br><br>"
                f"Thank you {ticket.full_name}<br><br>"
                f"Your support ticket <strong>{ticket.ticket_id}</strong> has been created successfully.<br><br>"
                f"A confirmation email has been sent to {ticket.email}<br><br>"
                "Our team usually replies within 24 hours."
            )
            messages.success(request, success_toast)

        return redirect('marketplace:contact')


def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(ContactMessage, ticket_id=ticket_id)
    
    if request.method == 'POST':
        raw_message = request.POST.get('message', '').strip()
        message_text = escape(strip_tags(raw_message))
        
        if not message_text:
            messages.error(request, "Please enter a message.")
            return redirect('marketplace:ticket_detail', ticket_id=ticket_id)
            
        ContactReply.objects.create(
            ticket=ticket,
            sender=ticket.full_name,
            is_admin=False,
            content=message_text
        )
        
        ticket.status = 'open'
        ticket.is_read = False
        ticket.save(update_fields=['status', 'is_read'])
        
        from_email = settings.DEFAULT_FROM_EMAIL or 'tusharshrivas7999@gmail.com'
        admin_email = 'tusharshrivas7999@gmail.com'
        
        from django.urls import reverse
        admin_path = reverse('admin:marketplace_contactmessage_change', args=[ticket.id])
        admin_url = request.build_absolute_uri(admin_path)
        
        subject = f"📩 Customer Replied to Ticket - {ticket.ticket_id}"
        body = (
            f"Customer {ticket.full_name} has posted a new reply to Ticket {ticket.ticket_id}.\n\n"
            f"Message:\n{message_text}\n\n"
            f"Open Admin Dashboard: {admin_url}"
        )
        try:
            from django.core.mail import send_mail
            send_mail(subject, body, from_email, [admin_email], fail_silently=False)
        except Exception:
            pass
            
        messages.success(request, "Your reply has been posted successfully!")
        return redirect('marketplace:ticket_detail', ticket_id=ticket_id)
        
    replies = ticket.replies.all().order_by('created_at')
    context = {
        'ticket': ticket,
        'replies': replies,
    }
    return render(request, 'ticket_detail.html', context)


# Custom Admin Area Views (Check if User is staff or superuser)
def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def custom_admin_dashboard(request):
    products = Product.objects.all().order_by('-created_at')
    orders = Order.objects.all().order_by('-created_at')
    
    # Calculate statistics
    total_sales = Order.objects.filter(payment_status='Completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_downloads = Product.objects.aggregate(Sum('downloads_count'))['downloads_count__sum'] or 0
    
    # Category Distribution
    categories = Category.objects.annotate(num_products=Count('products'))
    
    context = {
        'products': products,
        'orders': orders[:10], # Show last 10 orders
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_downloads': total_downloads,
        'categories': categories,
    }
    return render(request, 'admin_custom/dashboard.html', context)

@login_required
@user_passes_test(is_admin, login_url='accounts:login')
def custom_admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product.price = float(data.get('price', product.price))
            product.old_price = float(data.get('old_price')) if data.get('old_price') else None
            product.stock_status = data.get('stock_status', product.stock_status)
            product.is_featured = bool(data.get('is_featured', product.is_featured))
            product.is_trending = bool(data.get('is_trending', product.is_trending))
            product.save()
            return JsonResponse({'status': 'success', 'message': 'Product updated successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
