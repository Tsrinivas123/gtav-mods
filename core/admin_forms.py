from django import forms
from django.utils.text import slugify
from marketplace.models import Product, Category
from blog.models import BlogPost


class ProductAdminForm(forms.ModelForm):
    """
    Unified admin form for Creating AND Editing a product.
    - Pass instance=product for edit mode (duplicate checks exclude self).
    - slug is auto-generated from name if left blank.
    - main_image excluded until Phase 2.3.
    """

    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'category', 'short_description', 'description',
            'requirements', 'installation_guide', 'price', 'old_price',
            'stock_status', 'is_featured', 'is_trending',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'e.g. Ultra Realistic Car Pack v3',
                'id': 'id_name',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'auto-generated from name',
                'id': 'id_slug',
            }),
            'category': forms.Select(attrs={
                'class': 'admin-form-input',
                'id': 'id_category',
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'One-line summary shown on listing cards (max 255 chars)',
                'id': 'id_short_description',
            }),
            'description': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 6,
                'placeholder': 'Full description of the mod...',
                'id': 'id_description',
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 4,
                'placeholder': 'e.g. ScriptHookV v1.0.617.1, OpenIV 4.1',
                'id': 'id_requirements',
            }),
            'installation_guide': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 4,
                'placeholder': 'Step-by-step installation instructions...',
                'id': 'id_installation_guide',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'admin-form-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
                'id': 'id_price',
            }),
            'old_price': forms.NumberInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'Optional – original price for strike-through',
                'step': '0.01',
                'min': '0',
                'id': 'id_old_price',
            }),
            'stock_status': forms.Select(attrs={
                'class': 'admin-form-input',
                'id': 'id_stock_status',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'admin-form-checkbox',
                'id': 'id_is_featured',
            }),
            'is_trending': forms.CheckboxInput(attrs={
                'class': 'admin-form-checkbox',
                'id': 'id_is_trending',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Product.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'A product named "{name}" already exists. Use a unique name.'
            )
        return name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        name = self.data.get('name', '')
        if not slug:
            slug = slugify(name)
        if not slug:
            raise forms.ValidationError('Slug could not be generated. Enter a product name first.')
        qs = Product.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'The slug "{slug}" is already taken. Choose a different name or edit the slug.'
            )
        return slug

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price

    def clean_old_price(self):
        old_price = self.cleaned_data.get('old_price')
        if old_price is not None and old_price < 0:
            raise forms.ValidationError('Old price cannot be negative.')
        return old_price

    def clean(self):
        cleaned = super().clean()
        price     = cleaned.get('price')
        old_price = cleaned.get('old_price')
        if price is not None and old_price is not None:
            if old_price <= price:
                self.add_error(
                    'old_price',
                    'Old price should be greater than the current price to show a discount badge.'
                )
        return cleaned


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            'name', 'slug', 'description', 'icon', 'image',
            'seo_title', 'meta_description', 'meta_keywords',
            'display_order', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'e.g. Vehicles',
                'id': 'id_name',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'auto-generated from name',
                'id': 'id_slug',
            }),
            'description': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 4,
                'placeholder': 'Brief description of the category...',
                'id': 'id_description',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'e.g. fa-car',
                'id': 'id_icon',
            }),
            'seo_title': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'Optional SEO meta title override',
                'id': 'id_seo_title',
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 3,
                'placeholder': 'Search engine description tag',
                'id': 'id_meta_description',
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'gta 5 mods, vehicles, cars (comma-separated)',
                'id': 'id_meta_keywords',
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'admin-form-input',
                'placeholder': '0',
                'min': '0',
                'id': 'id_display_order',
            }),
            'status': forms.Select(attrs={
                'class': 'admin-form-input',
                'id': 'id_status',
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Category.objects.filter(name__iexact=name)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'A category named "{name}" already exists. Use a unique name.'
            )
        return name

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        name = self.data.get('name', '')
        if not slug:
            slug = slugify(name)
        if not slug:
            raise forms.ValidationError('Slug could not be generated. Enter a name first.')
        
        qs = Category.objects.filter(slug__iexact=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'The slug "{slug}" is already taken. Choose a different name or edit the slug.'
            )
        return slug


class BlogAdminForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = [
            'title', 'slug', 'excerpt', 'content', 'featured_image',
            'category', 'tags', 'author', 'status', 'publish_date',
            'seo_title', 'meta_description', 'meta_keywords',
            'canonical_url', 'og_title', 'og_description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'Enter blog title',
                'id': 'id_title',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'auto-generated from title',
                'id': 'id_slug',
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 3,
                'placeholder': 'Short summary or teaser...',
                'id': 'id_excerpt',
            }),
            'content': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'id': 'id_content',
                'style': 'display:none;',
            }),
            'category': forms.Select(attrs={
                'class': 'admin-form-input',
                'id': 'id_category',
            }),
            'tags': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'gta5, scripts, update (comma-separated)',
                'id': 'id_tags',
            }),
            'author': forms.Select(attrs={
                'class': 'admin-form-input',
                'id': 'id_author',
            }),
            'status': forms.Select(attrs={
                'class': 'admin-form-input',
                'id': 'id_status',
            }),
            'publish_date': forms.DateTimeInput(attrs={
                'class': 'admin-form-input',
                'type': 'datetime-local',
                'id': 'id_publish_date',
            }),
            'seo_title': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'Search engine title override',
                'id': 'id_seo_title',
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 3,
                'placeholder': 'Search engine description tag',
                'id': 'id_meta_description',
            }),
            'meta_keywords': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'keywords (comma-separated)',
                'id': 'id_meta_keywords',
            }),
            'canonical_url': forms.URLInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'https://example.com/canonical-url',
                'id': 'id_canonical_url',
            }),
            'og_title': forms.TextInput(attrs={
                'class': 'admin-form-input',
                'placeholder': 'Open Graph title',
                'id': 'id_og_title',
            }),
            'og_description': forms.Textarea(attrs={
                'class': 'admin-form-input',
                'rows': 3,
                'placeholder': 'Open Graph description',
                'id': 'id_og_description',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.publish_date:
            self.initial['publish_date'] = self.instance.publish_date.strftime('%Y-%m-%dT%H:%M')

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        qs = BlogPost.objects.filter(title__iexact=title)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'A blog post with the title "{title}" already exists. Use a unique title.'
            )
        return title

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        title = self.data.get('title', '')
        if not slug:
            slug = slugify(title)
        if not slug:
            raise forms.ValidationError('Slug could not be generated. Enter a title first.')
        
        qs = BlogPost.objects.filter(slug__iexact=slug)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f'The slug "{slug}" is already taken. Choose a different title or edit the slug.'
            )
        return slug
