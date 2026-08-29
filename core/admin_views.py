from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.text import slugify
from marketplace.models import Product, Category
from orders.models import Order, Coupon
from blog.models import BlogPost
from functools import wraps
import datetime


# ─── Admin Guard ───────────────────────────────────────────────────────────────

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access the admin panel.")
            return redirect('accounts:login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "You do not have permission to access this area.")
            return redirect('accounts:profile')
        return view_func(request, *args, **kwargs)
    return _wrapped


def _base_ctx():
    from marketplace.models import ContactMessage
    from marketplace.views import close_inactive_tickets
    try:
        close_inactive_tickets()
    except Exception:
        pass
    return {
        'pending_orders_count': Order.objects.filter(status='pending').count(),
        'unread_support_count': ContactMessage.objects.filter(is_read=False).count(),
    }



# ─── Dashboard ─────────────────────────────────────────────────────────────────

@admin_required
def dashboard_home(request):
    context = {
        **_base_ctx(),
        'page_title':       'Dashboard',
        'breadcrumb':       [('Dashboard', None)],
        'total_products':   Product.objects.count(),
        'total_orders':     Order.objects.count(),
        'total_revenue':    Order.objects.filter(status='completed')
                                .aggregate(t=Sum('total_amount'))['t'] or 0,
        'total_users':      User.objects.count(),
        'total_downloads':  Product.objects.aggregate(t=Sum('downloads_count'))['t'] or 0,
        'total_categories': Category.objects.count(),
        'total_blog_posts': BlogPost.objects.count(),
        'total_coupons':    Coupon.objects.filter(active=True).count(),
        'recent_orders':    Order.objects.select_related('user').order_by('-created_at')[:8],
        'recent_products':  Product.objects.select_related('category').order_by('-created_at')[:6],
    }
    return render(request, 'admin_custom/dashboard.html', context)


# ─── Product List ──────────────────────────────────────────────────────────────

@admin_required
def admin_products(request):
    qs = Product.objects.select_related('category').order_by('-created_at')

    q           = request.GET.get('q', '').strip()
    cat_filter  = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    featured_filter = request.GET.get('featured', '')
    trending_filter = request.GET.get('trending', '')

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(short_description__icontains=q) | Q(category__name__icontains=q))
    if cat_filter:
        qs = qs.filter(category__slug=cat_filter)
    if status_filter:
        qs = qs.filter(stock_status=status_filter)
    if featured_filter == '1':
        qs = qs.filter(is_featured=True)
    if trending_filter == '1':
        qs = qs.filter(is_trending=True)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'admin_custom/products.html', {
        **_base_ctx(),
        'page_title':       'Products',
        'breadcrumb':       [('Dashboard', 'custom_admin:dashboard'), ('Products', None)],
        'products':         page_obj,
        'page_obj':         page_obj,
        'total_count':      paginator.count,
        'categories':       Category.objects.all(),
        'q':                q,
        'cat_filter':       cat_filter,
        'status_filter':    status_filter,
        'featured_filter':  featured_filter,
        'trending_filter':  trending_filter,
        'status_choices':   Product.STOCK_CHOICES,
    })


# ─── Add Product ───────────────────────────────────────────────────────────────

@admin_required
def admin_product_add(request):
    from core.admin_forms import ProductAdminForm
    if request.method == 'POST':
        form = ProductAdminForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            # Phase 2.3 will handle image upload; use placeholder for now
            if not product.main_image:
                product.main_image = 'products/placeholder.jpg'
            product.save()
            messages.success(request, f'✔ Product "{product.name}" created successfully! You can now manage its media and files below.')
            return redirect('custom_admin:product_edit', product_id=product.id)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProductAdminForm()

    return render(request, 'admin_custom/product_form.html', {
        **_base_ctx(),
        'page_title': 'Add Product',
        'breadcrumb': [('Dashboard', 'custom_admin:dashboard'), ('Products', 'custom_admin:products'), ('Add Product', None)],
        'form': form,
        'mode': 'add',
    })


# ─── Edit Product ──────────────────────────────────────────────────────────────

@admin_required
def admin_product_edit(request, product_id):
    from core.admin_forms import ProductAdminForm
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ProductAdminForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'✔ Product "{product.name}" updated successfully!')
            return redirect('custom_admin:products')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = ProductAdminForm(instance=product)

    return render(request, 'admin_custom/product_form.html', {
        **_base_ctx(),
        'page_title': f'Edit: {product.name}',
        'breadcrumb': [('Dashboard', 'custom_admin:dashboard'), ('Products', 'custom_admin:products'), ('Edit Product', None)],
        'form': form,
        'product': product,
        'mode': 'edit',
    })


# ─── Delete Product ────────────────────────────────────────────────────────────

@admin_required
def admin_product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        name = product.name
        product.is_deleted = True
        product.slug = f"deleted-{product.slug}-{int(datetime.datetime.now().timestamp())}"
        product.save()
        messages.success(request, f'✔ Product "{name}" was successfully deleted.')
    else:
        messages.warning(request, 'Invalid delete request.')
    return redirect('custom_admin:products')


# ─── Duplicate Product ─────────────────────────────────────────────────────────

@admin_required
def admin_product_duplicate(request, product_id):
    original = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        # Build unique slug
        base_slug = f"copy-{original.slug}"
        slug      = base_slug
        counter   = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Build unique name
        base_name = f"Copy of {original.name}"
        name      = base_name
        counter   = 1
        while Product.objects.filter(name__iexact=name).exists():
            name = f"{base_name} ({counter})"
            counter += 1

        Product.objects.create(
            name              = name,
            slug              = slug,
            category          = original.category,
            short_description = original.short_description,
            description       = original.description,
            requirements      = original.requirements,
            installation_guide = original.installation_guide,
            price             = original.price,
            old_price         = original.old_price,
            stock_status      = 'coming_soon',   # duplicates start as "coming soon" / draft
            is_featured       = False,
            is_trending       = False,
            main_image        = original.main_image or 'products/placeholder.jpg',
            downloads_count   = 0,
            is_deleted        = False,
        )
        messages.success(request, f'✔ "{original.name}" duplicated. Edit the copy to make it live.')
    return redirect('custom_admin:products')


# ─── Bulk Actions ──────────────────────────────────────────────────────────────

@admin_required
def admin_product_bulk(request):
    if request.method != 'POST':
        return redirect('custom_admin:products')

    action      = request.POST.get('bulk_action', '')
    product_ids = request.POST.getlist('product_ids')

    if not product_ids:
        messages.warning(request, 'No products selected.')
        return redirect('custom_admin:products')

    qs = Product.objects.filter(pk__in=product_ids)
    count = qs.count()

    if action == 'publish':
        qs.update(stock_status='available')
        messages.success(request, f'✔ {count} product(s) published (set to Available).')
    elif action == 'draft':
        qs.update(stock_status='coming_soon')
        messages.success(request, f'✔ {count} product(s) moved to Draft (Coming Soon).')
    elif action == 'delete':
        for p in qs:
            p.is_deleted = True
            p.slug = f"deleted-{p.slug}-{int(datetime.datetime.now().timestamp())}"
            p.save()
        messages.success(request, f'✔ {count} product(s) successfully deleted.')
    elif action == 'feature':
        qs.update(is_featured=True)
        messages.success(request, f'✔ {count} product(s) marked as Featured.')
    elif action == 'unfeature':
        qs.update(is_featured=False)
        messages.success(request, f'✔ {count} product(s) removed from Featured.')
    else:
        messages.warning(request, 'Unknown bulk action.')

    return redirect('custom_admin:products')


# ─── Categories ────────────────────────────────────────────────────────────────

from core.admin_forms import CategoryAdminForm
from django.db.models import Count

@admin_required
def admin_categories(request):
    categories = Category.objects.annotate(product_count=Count('products'))

    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        categories = categories.filter(name__icontains=search_query)

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        categories = categories.filter(status=status_filter)

    # Sorting
    sort_by = request.GET.get('sort_by', 'order').strip()
    if sort_by == 'name':
        categories = categories.order_by('name')
    elif sort_by == 'name_desc':
        categories = categories.order_by('-name')
    elif sort_by == 'created':
        categories = categories.order_by('created_at')
    elif sort_by == 'created_desc':
        categories = categories.order_by('-created_at')
    elif sort_by == 'products_count':
        categories = categories.order_by('product_count')
    elif sort_by == 'products_count_desc':
        categories = categories.order_by('-product_count')
    else:
        categories = categories.order_by('display_order', 'name')

    total_count = categories.count()

    # Pagination
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_custom/categories.html', {
        **_base_ctx(),
        'page_title':  'Category Management',
        'breadcrumb':  [('Dashboard', 'custom_admin:dashboard'), ('Categories', None)],
        'categories':  page_obj,
        'total_count': total_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort_by': sort_by,
    })


@admin_required
def admin_category_add(request):
    if request.method == 'POST':
        form = CategoryAdminForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'✔ Category "{category.name}" created successfully!')
            return redirect('custom_admin:categories')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = CategoryAdminForm()

    return render(request, 'admin_custom/category_form.html', {
        **_base_ctx(),
        'page_title': 'Add Category',
        'breadcrumb': [
            ('Dashboard', 'custom_admin:dashboard'),
            ('Categories', 'custom_admin:categories'),
            ('Add Category', None)
        ],
        'form': form,
        'mode': 'add',
    })


@admin_required
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    if request.method == 'POST':
        form = CategoryAdminForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'✔ Category "{category.name}" updated successfully!')
            return redirect('custom_admin:categories')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = CategoryAdminForm(instance=category)

    return render(request, 'admin_custom/category_form.html', {
        **_base_ctx(),
        'page_title': 'Edit Category',
        'breadcrumb': [
            ('Dashboard', 'custom_admin:dashboard'),
            ('Categories', 'custom_admin:categories'),
            ('Edit Category', None)
        ],
        'form': form,
        'category': category,
        'mode': 'edit',
    })


@admin_required
def admin_category_delete(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    product_count = category.products.count()

    if request.method == 'POST':
        if product_count > 0:
            target_cat_id = request.POST.get('target_category')
            if not target_cat_id:
                messages.error(request, 'You must select a target category to move the products to.')
                return redirect('custom_admin:category_delete', category_id=category_id)
            
            target_cat = get_object_or_404(Category, pk=target_cat_id)
            if target_cat == category:
                messages.error(request, 'Cannot move products to the same category being deleted.')
                return redirect('custom_admin:category_delete', category_id=category_id)
                
            category.products.all().update(category=target_cat)
            
        category.delete()
        messages.success(request, f'✔ Category "{category.name}" deleted successfully!')
        return redirect('custom_admin:categories')

    other_categories = Category.objects.exclude(pk=category_id)
    
    return render(request, 'admin_custom/category_delete.html', {
        **_base_ctx(),
        'page_title': 'Delete Category',
        'breadcrumb': [
            ('Dashboard', 'custom_admin:dashboard'),
            ('Categories', 'custom_admin:categories'),
            ('Delete Category', None)
        ],
        'category': category,
        'product_count': product_count,
        'other_categories': other_categories,
    })


# ─── Orders ────────────────────────────────────────────────────────────────────

@admin_required
def admin_orders(request):
    orders = Order.objects.select_related('user', 'coupon').order_by('-created_at')
    return render(request, 'admin_custom/orders.html', {
        **_base_ctx(),
        'page_title':  'Orders',
        'breadcrumb':  [('Dashboard', 'custom_admin:dashboard'), ('Orders', None)],
        'orders':      orders,
        'total_count': orders.count(),
    })


# ─── Customers ─────────────────────────────────────────────────────────────────

@admin_required
def admin_customers(request):
    customers = User.objects.filter(is_staff=False, is_superuser=False).order_by('-date_joined')
    return render(request, 'admin_custom/customers.html', {
        **_base_ctx(),
        'page_title':  'Customers',
        'breadcrumb':  [('Dashboard', 'custom_admin:dashboard'), ('Customers', None)],
        'customers':   customers,
        'total_count': customers.count(),
    })


# ─── Blog ──────────────────────────────────────────────────────────────────────

from core.admin_forms import BlogAdminForm

@admin_required
def admin_blog(request):
    posts = BlogPost.objects.select_related('author')

    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        posts = posts.filter(status=status_filter)

    # Category filter
    category_filter = request.GET.get('category', '').strip()
    if category_filter:
        posts = posts.filter(category=category_filter)

    # Sorting
    sort_by = request.GET.get('sort_by', 'newest').strip()
    if sort_by == 'title':
        posts = posts.order_by('title')
    elif sort_by == 'title_desc':
        posts = posts.order_by('-title')
    elif sort_by == 'views':
        posts = posts.order_by('-views_count')
    elif sort_by == 'oldest':
        posts = posts.order_by('created_at')
    else: # newest
        posts = posts.order_by('-created_at')

    total_count = posts.count()

    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_custom/blog.html', {
        **_base_ctx(),
        'page_title':  'Blog Management',
        'breadcrumb':  [('Dashboard', 'custom_admin:dashboard'), ('Blog', None)],
        'posts':       page_obj,
        'total_count': total_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'category_choices': BlogPost.CATEGORY_CHOICES,
    })


@admin_required
def admin_blog_add(request):
    if request.method == 'POST':
        form = BlogAdminForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save()
            messages.success(request, f'✔ Blog post "{post.title}" created successfully!')
            return redirect('custom_admin:blog')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = BlogAdminForm(initial={'author': request.user})

    return render(request, 'admin_custom/blog_form.html', {
        **_base_ctx(),
        'page_title': 'Add Blog Post',
        'breadcrumb': [
            ('Dashboard', 'custom_admin:dashboard'),
            ('Blog', 'custom_admin:blog'),
            ('Add Post', None)
        ],
        'form': form,
        'mode': 'add',
    })


@admin_required
def admin_blog_edit(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    if request.method == 'POST':
        form = BlogAdminForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            messages.success(request, f'✔ Blog post "{post.title}" updated successfully!')
            return redirect('custom_admin:blog')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = BlogAdminForm(instance=post)

    return render(request, 'admin_custom/blog_form.html', {
        **_base_ctx(),
        'page_title': 'Edit Blog Post',
        'breadcrumb': [
            ('Dashboard', 'custom_admin:dashboard'),
            ('Blog', 'custom_admin:blog'),
            ('Edit Post', None)
        ],
        'form': form,
        'post': post,
        'mode': 'edit',
    })


@admin_required
def admin_blog_delete(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    if request.method == 'POST':
        post.delete()
        messages.success(request, f'✔ Blog post "{post.title}" deleted successfully!')
        return redirect('custom_admin:blog')

    return render(request, 'admin_custom/blog_delete.html', {
        **_base_ctx(),
        'page_title': 'Delete Blog Post',
        'breadcrumb': [
            ('Dashboard', 'custom_admin:dashboard'),
            ('Blog', 'custom_admin:blog'),
            ('Delete Post', None)
        ],
        'post': post,
    })


# ─── Coupons ───────────────────────────────────────────────────────────────────

@admin_required
def admin_coupons(request):
    coupons = Coupon.objects.order_by('-id')
    return render(request, 'admin_custom/coupons.html', {
        **_base_ctx(),
        'page_title':  'Coupons',
        'breadcrumb':  [('Dashboard', 'custom_admin:dashboard'), ('Coupons', None)],
        'coupons':     coupons,
        'total_count': coupons.count(),
    })


# ─── Membership ────────────────────────────────────────────────────────────────

@admin_required
def admin_membership(request):
    from accounts.models import Profile
    premium_users = Profile.objects.filter(membership_type__in=['premium', 'legend'])
    return render(request, 'admin_custom/membership.html', {
        **_base_ctx(),
        'page_title':    'Membership',
        'breadcrumb':    [('Dashboard', 'custom_admin:dashboard'), ('Membership', None)],
        'premium_users': premium_users,
        'total_count':   premium_users.count(),
    })


# ─── Analytics ─────────────────────────────────────────────────────────────────

@admin_required
def admin_analytics(request):
    from django.utils import timezone
    from django.db.models import Count

    seven_days_ago = timezone.now() - datetime.timedelta(days=7)
    daily_orders   = (
        Order.objects.filter(created_at__gte=seven_days_ago)
        .extra(select={'day': "date(created_at)"})
        .values('day')
        .annotate(count=Count('id'), revenue=Sum('total_amount'))
        .order_by('day')
    )
    top_products = Product.objects.order_by('-downloads_count')[:10]

    return render(request, 'admin_custom/analytics.html', {
        **_base_ctx(),
        'page_title':   'Analytics',
        'breadcrumb':   [('Dashboard', 'custom_admin:dashboard'), ('Analytics', None)],
        'daily_orders': list(daily_orders),
        'top_products': top_products,
    })


# ─── Settings ──────────────────────────────────────────────────────────────────

@admin_required
def admin_settings(request):
    from marketplace.models import SiteSetting
    if request.method == 'POST':
        enable_coupons = request.POST.get('enable_coupons') == 'on'
        SiteSetting.set_setting('enable_coupons', str(enable_coupons))
        messages.success(request, '✔ Settings updated successfully.')
        return redirect('custom_admin:settings')
        
    enable_coupons = SiteSetting.get_setting('enable_coupons', 'False').lower() == 'true'
    
    return render(request, 'admin_custom/settings.html', {
        **_base_ctx(),
        'page_title': 'Settings',
        'breadcrumb': [('Dashboard', 'custom_admin:dashboard'), ('Settings', None)],
        'enable_coupons': enable_coupons,
    })


# ─── Orders Management – Phase 4 ───────────────────────────────────────────────

@admin_required
def admin_orders(request):
    qs = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(code__icontains=q) |
            Q(invoice_number__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q)
        )

    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    payment_filter = request.GET.get('payment_status', '')
    if payment_filter:
        qs = qs.filter(payment_status=payment_filter)

    gateway_filter = request.GET.get('gateway', '')
    if gateway_filter:
        qs = qs.filter(payment_method=gateway_filter)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    revenue = qs.filter(payment_status='Success').aggregate(t=Sum('total_amount'))['t'] or 0

    return render(request, 'admin_custom/orders.html', {
        **_base_ctx(),
        'page_title':     'Orders',
        'breadcrumb':     [('Dashboard', 'custom_admin:dashboard'), ('Orders', None)],
        'orders':         page_obj,
        'page_obj':       page_obj,
        'total_count':    qs.count(),
        'total_revenue':  revenue,
        'q':              q,
        'status_filter':  status_filter,
        'payment_filter': payment_filter,
        'gateway_filter': gateway_filter,
    })


@admin_required
def admin_order_detail(request, order_code):
    order = get_object_or_404(Order, code=order_code)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_payment_status = request.POST.get('payment_status')

        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
        if new_payment_status and new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES):
            order.payment_status = new_payment_status
        order.save()
        messages.success(request, f'✔ Order {order.code} updated successfully.')
        return redirect('custom_admin:order_detail', order_code=order.code)

    return render(request, 'admin_custom/order_detail.html', {
        **_base_ctx(),
        'page_title': f'Order {order.code}',
        'breadcrumb': [
            ('Dashboard', 'custom_admin:dashboard'),
            ('Orders', 'custom_admin:orders'),
            (order.code, None),
        ],
        'order':               order,
        'status_choices':      Order.STATUS_CHOICES,
        'payment_status_choices': Order.PAYMENT_STATUS_CHOICES,
    })


# ─── Customers ──────────────────────────────────────────────────────────────────

@admin_required
def admin_customers(request):
    from accounts.models import Profile
    q = request.GET.get('q', '').strip()
    users = User.objects.order_by('-date_joined')
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        )
    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'admin_custom/customers.html', {
        **_base_ctx(),
        'page_title':  'Customers',
        'breadcrumb':  [('Dashboard', 'custom_admin:dashboard'), ('Customers', None)],
        'users':       page_obj,
        'page_obj':    page_obj,
        'total_count': users.count(),
        'q':           q,
    })

