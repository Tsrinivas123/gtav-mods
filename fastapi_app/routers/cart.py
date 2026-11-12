from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product
from ..schemas import CartCalculateIn, CartCalculateOut, CartItemDetail

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])

@router.post("/calculate", response_model=CartCalculateOut)
def calculate_cart(cart_data: CartCalculateIn, db: Session = Depends(get_db)):
    """Calculate cart items subtotal, discounts, and item breakdowns."""
    if not cart_data.items:
        return CartCalculateOut(
            items=[],
            subtotal=0.0,
            discount=0.0,
            final_total=0.0,
            total_count=0
        )

    product_ids = [item.product_id for item in cart_data.items]
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}

    calculated_items = []
    subtotal = 0.0
    total_count = 0

    for item in cart_data.items:
        product = products.get(item.product_id)
        if product:
            p_price = float(product.price)
            item_total = p_price * item.quantity
            subtotal += item_total
            total_count += item.quantity
            calculated_items.append(CartItemDetail(
                product_id=product.id,
                name=product.name,
                slug=product.slug,
                price=p_price,
                quantity=item.quantity,
                total=round(item_total, 2),
                image=product.main_image
            ))

    discount = 0.0
    # Optional coupon code logic
    if cart_data.coupon_code and cart_data.coupon_code.strip().upper() == "PAWAN10":
        discount = round(subtotal * 0.10, 2)

    final_total = max(0.0, round(subtotal - discount, 2))

    return CartCalculateOut(
        items=calculated_items,
        subtotal=round(subtotal, 2),
        discount=discount,
        final_total=final_total,
        total_count=total_count
    )

