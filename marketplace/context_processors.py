from .models import Product, SiteSetting

def cart_context(request):
    """
    Globally context processor for the shopping cart.
    Keeps track of cart items, quantities, and totals using request.session.
    """
    cart = request.session.get('cart', {})
    cart_items = []
    cart_total = 0
    cart_count = 0

    if cart:
        product_ids = cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        
        for product in products:
            quantity = cart[str(product.id)]
            total = product.price * quantity
            cart_total += total
            cart_count += quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total': total,
            })

    coupons_enabled = SiteSetting.get_setting('enable_coupons', 'False').lower() == 'true'

    return {
        'cart_count': cart_count,
        'cart_items': cart_items,
        'cart_total': cart_total,
        'coupons_enabled': coupons_enabled,
    }
