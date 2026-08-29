from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
import re

class BlogPost(models.Model):
    CATEGORY_CHOICES = (
        ('guides', 'Guides & Tutorials'),
        ('news', 'News & Updates'),
        ('showcase', 'Mod Showcases'),
        ('optimization', 'Performance & Optimization'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(help_text="Short teaser summarizing the post")
    featured_image = models.ImageField(upload_to='blog/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='guides')
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # New Phase 3.2 fields
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='blog_posts')
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', blank=True)
    publish_date = models.DateTimeField(default=timezone.now, blank=True)
    
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    canonical_url = models.URLField(blank=True)
    og_title = models.CharField(max_length=200, blank=True)
    og_description = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def reading_time(self):
        """Estimate reading time based on word count (~200 words per minute)."""
        if not self.content:
            return 1
        clean_text = re.sub(r'<[^>]+>', '', self.content)
        words = len(re.findall(r'\w+', clean_text))
        return max(1, int(words / 200 + 0.5))

class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"
