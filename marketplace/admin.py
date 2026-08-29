from django.contrib import admin
from .models import Category, Product, ProductImage, VersionHistory, Review

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class VersionHistoryInline(admin.TabularInline):
    model = VersionHistory
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'downloads_count', 'stock_status', 'is_featured', 'is_trending', 'created_at')
    list_filter = ('category', 'stock_status', 'is_featured', 'is_trending')
    search_fields = ('name', 'short_description', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, VersionHistoryInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'content')


from django.conf import settings
from django.urls import reverse
from .models import ContactMessage, ContactReply

class ContactReplyInline(admin.TabularInline):
    model = ContactReply
    extra = 1
    readonly_fields = ('created_at', 'is_admin', 'sender')
    fields = ('sender', 'is_admin', 'content', 'created_at')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'full_name', 'email', 'subject', 'category', 'status', 'created_at', 'is_read')
    list_filter = ('status', 'is_read', 'created_at', 'category')
    search_fields = ('ticket_id', 'full_name', 'email', 'subject', 'category')
    ordering = ['-created_at']
    readonly_fields = ('ticket_id', 'full_name', 'email', 'category', 'subject', 'message', 'ip_address', 'created_at', 'updated_at')
    
    inlines = [ContactReplyInline]

    actions = ['mark_as_read', 'mark_as_unread', 'close_tickets']

    @admin.action(description="Mark selected tickets as Read")
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, "Selected tickets marked as Read.")

    @admin.action(description="Mark selected tickets as Unread")
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, "Selected tickets marked as Unread.")

    @admin.action(description="Close selected tickets")
    def close_tickets(self, request, queryset):
        queryset.update(status='closed')
        self.message_user(request, "Selected tickets closed.")

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if obj and not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=['is_read'])
        return super().change_view(request, object_id, form_url, extra_context)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, ContactReply):
                if not instance.id:
                    instance.sender = f"PawanMod Support ({request.user.get_full_name() or request.user.username})"
                    instance.is_admin = True
                instance.save()
                
                ticket = instance.ticket
                from_email = settings.DEFAULT_FROM_EMAIL or 'tusharshrivas7999@gmail.com'
                ticket_url = request.build_absolute_uri(reverse('marketplace:ticket_detail', args=[ticket.ticket_id]))
                
                subject = f"Re: PawanMod Support - Ticket {ticket.ticket_id}"
                body = (
                    f"Hi {ticket.full_name},\n\n"
                    "Our support team has posted a reply to your request:\n\n"
                    f"\"{instance.content}\"\n\n"
                    f"You can view the full conversation history and respond to this ticket directly at:\n"
                    f"{ticket_url}\n\n"
                    "Regards,\n"
                    "PawanMod Support Team\n"
                    "https://pawanmod.com"
                )
                try:
                    from django.core.mail import send_mail
                    send_mail(subject, body, from_email, [ticket.email], fail_silently=False)
                except Exception:
                    pass
                    
        formset.save_m2m()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from marketplace.views import close_inactive_tickets
        try:
            close_inactive_tickets()
        except Exception:
            pass
            
        extra_context['unread_count'] = ContactMessage.objects.filter(is_read=False).count()
        extra_context['open_count'] = ContactMessage.objects.filter(status='open').count()
        extra_context['in_progress_count'] = ContactMessage.objects.filter(status='in_progress').count()
        extra_context['resolved_count'] = ContactMessage.objects.filter(status='resolved').count()
        extra_context['closed_count'] = ContactMessage.objects.filter(status='closed').count()
        
        return super().changelist_view(request, extra_context=extra_context)

