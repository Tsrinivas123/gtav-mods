from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Profile
from marketplace.models import Product
from orders.models import Order
import datetime

import uuid
import random

def user_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('custom_admin:dashboard')
        return redirect('accounts:profile')
        
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')
        
        username = username_or_email
        if '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                username = user_obj.username
            except User.DoesNotExist:
                pass
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if user.is_staff or user.is_superuser:
                return redirect('custom_admin:dashboard')
            next_url = request.GET.get('next', 'accounts:profile')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html')

def user_register(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, "Please enter an email address.")
            return render(request, 'login.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Please login instead.")
            return render(request, 'login.html')
            
        username = email.split('@')[0]
        if User.objects.filter(username=username).exists():
            username = f"{username}_{uuid.uuid4().hex[:4]}"
            
        # Set random password
        password = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))
        
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, f"Registration successful! Your auto-generated username is '{username}'. A password set link has been simulated.")
        return redirect('accounts:profile')
        
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('marketplace:home')

@login_required
def profile(request):
    # Fetch orders, wishlist, profile stats
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    wishlist = request.user.profile.wishlist.all()
    
    # Fetch all completed purchased items (OrderItem objects)
    from orders.models import OrderItem
    purchased_items = OrderItem.objects.filter(
        order__user=request.user,
        order__status__in=['paid', 'completed']
    ).select_related('order', 'product').order_by('-order__created_at')
    
    free_mods = Product.objects.filter(price=0.00, stock_status='available', is_deleted=False)
    
    context = {
        'orders': orders,
        'wishlist': wishlist,
        'purchased_items': purchased_items,
        'free_mods': free_mods,
        'profile': request.user.profile,
    }
    return render(request, 'dashboard.html', context)

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    profile = request.user.profile
    
    if profile.wishlist.filter(id=product.id).exists():
        profile.wishlist.remove(product)
        added = False
        message = "Removed from wishlist"
    else:
        profile.wishlist.add(product)
        added = True
        message = "Added to wishlist"
        
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'added': added, 'message': message})
        
    messages.success(request, message)
    return redirect(request.META.get('HTTP_REFERER', 'marketplace:store'))

@login_required
def buy_membership(request):
    if request.method == 'POST':
        tier = request.POST.get('tier')
        if tier not in ['premium', 'legend']:
            messages.error(request, "Invalid membership selection.")
            return redirect('accounts:profile')
            
        profile = request.user.profile
        profile.membership_type = tier
        # Add 30 days validation
        profile.membership_expires = timezone.now() + datetime.timedelta(days=30)
        profile.save()
        
        messages.success(request, f"Congratulations! You are now a {tier.upper()} member!")
        return redirect('accounts:profile')
        
    return redirect('marketplace:home')

@login_required
def profile_update(request):
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        
        user.email = request.POST.get('email', user.email)
        profile.billing_address = request.POST.get('billing_address', profile.billing_address)
        
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
            
        user.save()
        profile.save()
        messages.success(request, "Profile updated successfully.")
        
    return redirect('accounts:profile')
