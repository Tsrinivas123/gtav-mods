from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/coupon/apply/', views.apply_coupon, name='apply_coupon'),

    # Checkout & Payment
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/pay/<str:order_code>/', views.payment_gate, name='payment_gate'),
    path('checkout/complete/', views.payment_complete, name='payment_complete'),

    # Order
    path('order/<str:order_code>/', views.order_complete, name='order_complete'),
    path('order/<str:order_code>/invoice/', views.invoice_pdf, name='invoice_pdf'),

    # Secure download (increments downloads_count only on download)
    path('download/<int:version_id>/', views.download_file, name='download_file'),
]

