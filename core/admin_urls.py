from django.urls import path
from core import admin_views, admin_views_media

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard
    path('',  admin_views.dashboard_home, name='dashboard'),

    # ── Products – Phase 2.1 / 2.2 ─────────────────────────────────────────
    path('products/',                               admin_views.admin_products,        name='products'),
    path('products/add/',                           admin_views.admin_product_add,     name='product_add'),
    path('products/<int:product_id>/edit/',         admin_views.admin_product_edit,    name='product_edit'),
    path('products/<int:product_id>/delete/',       admin_views.admin_product_delete,  name='product_delete'),
    path('products/<int:product_id>/duplicate/',    admin_views.admin_product_duplicate, name='product_duplicate'),
    path('products/bulk/',                          admin_views.admin_product_bulk,    name='product_bulk'),

    # ── Products Media Management – Phase 2.3 ──────────────────────────────────
    path('products/<int:product_id>/media/main/upload/',       admin_views_media.upload_main_image, name='product_media_main_upload'),
    path('products/<int:product_id>/media/main/delete/',       admin_views_media.delete_main_image, name='product_media_main_delete'),
    path('products/<int:product_id>/media/gallery/upload/',    admin_views_media.upload_gallery,    name='product_media_gallery_upload'),
    path('products/<int:product_id>/media/gallery/delete/<int:image_id>/', admin_views_media.delete_gallery, name='product_media_gallery_delete'),
    path('products/<int:product_id>/media/gallery/reorder/',   admin_views_media.reorder_gallery,   name='product_media_gallery_reorder'),
    path('products/<int:product_id>/media/file/upload/',       admin_views_media.upload_file,       name='product_media_file_upload'),
    path('products/<int:product_id>/media/file/delete/',       admin_views_media.delete_file,       name='product_media_file_delete'),

    # ── Placeholder pages ──────────────────────────────────────────────────
    # ── Categories Management – Phase 3.1 ──────────────────────────────────────
    path('categories/',                        admin_views.admin_categories,      name='categories'),
    path('categories/add/',                    admin_views.admin_category_add,    name='category_add'),
    path('categories/<int:category_id>/edit/', admin_views.admin_category_edit,   name='category_edit'),
    path('categories/<int:category_id>/delete/', admin_views.admin_category_delete, name='category_delete'),
    path('orders/',                             admin_views.admin_orders,         name='orders'),
    path('orders/<str:order_code>/',             admin_views.admin_order_detail,   name='order_detail'),
    path('customers/',   admin_views.admin_customers,    name='customers'),
    # ── Blog Management – Phase 3.2 ──────────────────────────────────────────
    path('blog/',                              admin_views.admin_blog,            name='blog'),
    path('blog/add/',                          admin_views.admin_blog_add,        name='blog_add'),
    path('blog/<int:post_id>/edit/',           admin_views.admin_blog_edit,       name='blog_edit'),
    path('blog/<int:post_id>/delete/',         admin_views.admin_blog_delete,     name='blog_delete'),
    path('coupons/',     admin_views.admin_coupons,      name='coupons'),
    path('membership/',  admin_views.admin_membership,   name='membership'),
    path('analytics/',   admin_views.admin_analytics,    name='analytics'),
    path('settings/',    admin_views.admin_settings,     name='settings'),
]
