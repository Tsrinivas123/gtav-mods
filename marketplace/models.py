from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone

class Category(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, help_text="FontAwesome icon class, e.g. fa-car")
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    description = models.TextField(blank=True)
    
    # New Phase 3.1 fields
    seo_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    display_order = models.IntegerField(default=0, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['display_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ActiveProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Product(models.Model):
    STOCK_CHOICES = (
        ('available', 'Available'),
        ('coming_soon', 'Coming Soon'),
        ('deprecated', 'Deprecated'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    short_description = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(help_text="System requirements for the mod, e.g. ScriptHookV, OpenIV")
    installation_guide = models.TextField(help_text="Detailed steps to install this mod")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.0)])
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0.0)])
    downloads_count = models.IntegerField(default=0)
    stock_status = models.CharField(max_length=20, choices=STOCK_CHOICES, default='available')
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    main_image = models.ImageField(upload_to='products/images/')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveProductManager()
    all_objects = models.Manager()

    class Meta:
        base_manager_name = 'all_objects'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            discount = ((self.old_price - self.price) / self.old_price) * 100
            return int(round(discount))
        return 0

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum([r.rating for r in reviews]) / len(reviews), 1)
        return 4.5  # Premium default rating for demo display if no reviews exist

    @property
    def latest_version(self):
        """Returns the most recent VersionHistory entry for download link generation."""
        return self.versions.first()

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to='products/gallery/')
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} Screenshot"

class VersionHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=50)
    changelog = models.TextField()
    release_date = models.DateTimeField(auto_now_add=True)
    download_file = models.FileField(upload_to='products/files/', blank=True, null=True)
    download_url = models.URLField(blank=True, null=True, help_text="Fallback download link if file not uploaded")

    class Meta:
        verbose_name_plural = "Version Histories"
        ordering = ['-release_date']

    def __str__(self):
        return f"{self.product.name} v{self.version}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"


class ContactMessage(models.Model):
    CATEGORY_CHOICES = (
        ('payment', 'Payment Issue'),
        ('download', 'Download Issue'),
        ('installation', 'Installation Help'),
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('general', 'General Inquiry'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    ticket_id = models.CharField(max_length=20, unique=True, blank=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_read = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_id:
            last_msg = ContactMessage.objects.all().order_by('-id').first()
            if last_msg and last_msg.ticket_id:
                try:
                    last_num = int(last_msg.ticket_id.split('-')[1])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            self.ticket_id = f"PM-{next_num:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_id} - {self.full_name} ({self.status})"


class ContactReply(models.Model):
    ticket = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name='replies')
    sender = models.CharField(max_length=150)
    is_admin = models.BooleanField(default=False)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Reply by {self.sender} on {self.ticket.ticket_id}"


class SiteSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, default='')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_setting(cls, key, default=''):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value):
        cls.objects.update_or_create(key=key, defaults={'value': str(value)})

    def __str__(self):
        return f"{self.key}: {self.value}"


