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
    """Customer login disabled on public site. Redirect staff to admin login, guests to store."""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('custom_admin:dashboard')
        return redirect('marketplace:store')
    return redirect('custom_admin:login')

def user_register(request):
    """Customer registration disabled. Public storefront is guest-first."""
    return redirect('marketplace:store')

def user_logout(request):
    is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    logout(request)
    if is_admin:
        messages.info(request, "Logged out of admin panel.")
        return redirect('custom_admin:login')
    return redirect('marketplace:home')

def profile(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('custom_admin:dashboard')
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        wishlist = request.user.profile.wishlist.all()
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
    return redirect('marketplace:store')

def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        profile = request.user.profile
        if profile.wishlist.filter(id=product.id).exists():
            profile.wishlist.remove(product)
            added = False
            message = f"Removed {product.name} from wishlist."
        else:
            profile.wishlist.add(product)
            added = True
            message = f"Added {product.name} to wishlist."
    else:
        wishlist = request.session.get('wishlist', [])
        if product.id in wishlist:
            wishlist.remove(product.id)
            added = False
            message = f"Removed {product.name} from wishlist."
        else:
            wishlist.append(product.id)
            added = True
            message = f"Added {product.name} to wishlist."
        request.session['wishlist'] = wishlist

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
