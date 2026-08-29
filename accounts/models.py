from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from marketplace.models import Product

class Profile(models.Model):
    MEMBERSHIP_CHOICES = (
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('legend', 'Legend'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    membership_type = models.CharField(max_length=20, choices=MEMBERSHIP_CHOICES, default='free')
    membership_expires = models.DateTimeField(blank=True, null=True)
    billing_address = models.TextField(blank=True)
    wishlist = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by')

    @property
    def is_premium(self):
        # In a real app we would check if membership_expires is in the future.
        # For our premium dashboard demo, any membership other than 'free' is active.
        return self.membership_type in ['premium', 'legend']

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)
