from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from .models import BlogPost, BlogComment

def post_list(request):
    now = timezone.now()
    # Filter only published posts that are not scheduled in the future
    posts = BlogPost.objects.select_related('author').filter(
        status='published',
        publish_date__lte=now
    )
    categories = BlogPost.CATEGORY_CHOICES
    
    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(category__icontains=search_query)
        )
        
    # Category filter
    category_query = request.GET.get('category', '').strip()
    if category_query:
        posts = posts.filter(category=category_query)
        
    recent_posts = BlogPost.objects.filter(
        status='published',
        publish_date__lte=now
    ).order_by('-publish_date')[:5]
    
    popular_posts = BlogPost.objects.filter(
        status='published',
        publish_date__lte=now
    ).order_by('-views_count')[:5]
    
    # Pagination - 6 posts per page
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'categories': categories,
        'selected_category': category_query,
        'search_query': search_query,
        'recent_posts': recent_posts,
        'popular_posts': popular_posts,
    }
    return render(request, 'blog/list.html', context)

def post_detail(request, slug):
    from django.http import Http404
    now = timezone.now()
    is_staff = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
    
    # Staff can see all, guests can only see published and past/current scheduled
    if is_staff:
        post = get_object_or_404(BlogPost.objects.select_related('author').prefetch_related('comments'), slug=slug)
    else:
        post = get_object_or_404(
            BlogPost.objects.select_related('author').prefetch_related('comments'),
            slug=slug,
            status='published',
            publish_date__lte=now
        )
    
    # Increment views
    post.views_count += 1
    post.save(update_fields=['views_count'])
    
    recent_posts = BlogPost.objects.filter(
        status='published',
        publish_date__lte=now
    ).order_by('-publish_date').exclude(id=post.id)[:5]
    
    context = {
        'post': post,
        'recent_posts': recent_posts,
    }
    return render(request, 'blog/detail.html', context)

def submit_comment(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        content = request.POST.get('content')
        
        if not name or not email or not content:
            messages.error(request, "Please fill out all fields.")
            return redirect('blog:post_detail', slug=slug)
            
        BlogComment.objects.create(
            post=post,
            name=name,
            email=email,
            content=content
        )
        messages.success(request, "Comment posted successfully!")
    return redirect('blog:post_detail', slug=slug)
