from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.home, name='home'),
    path('store/', views.store, name='store'),
    path('store/<slug:slug>/', views.product_detail, name='product_detail'),
    path('store/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('categories/', views.categories_list, name='categories_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('membership/', views.membership_info, name='membership_info'),
    path('contact/', views.contact, name='contact'),
    path('support/ticket/<str:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('custom-admin/', views.custom_admin_dashboard, name='custom_admin'),
    path('custom-admin/product/edit/<int:pk>/', views.custom_admin_product_edit, name='custom_admin_product_edit'),
]
