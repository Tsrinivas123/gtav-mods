from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# Base Category
class CategoryBase(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = "fa-cube"
    description: Optional[str] = ""

class CategoryOut(CategoryBase):
    id: int
    product_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Reviews
class ReviewOut(BaseModel):
    id: int
    reviewer_name: str
    rating: int
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# Products
class ProductListItem(BaseModel):
    id: int
    name: str
    slug: str
    short_description: str
    price: float
    old_price: Optional[float] = None
    discount_percentage: Optional[int] = 0
    main_image: Optional[str] = None
    downloads_count: int
    stock_status: str
    is_featured: bool
    is_trending: bool
    category_slug: Optional[str] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductDetailOut(ProductListItem):
    description: str
    requirements: str
    installation_guide: str
    reviews: List[ReviewOut] = []
    average_rating: Optional[float] = None
    reviews_count: int = 0


# Cart Item Request & Calculation Response
class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)

class CartCalculateIn(BaseModel):
    items: List[CartItemIn]
    coupon_code: Optional[str] = None

class CartItemDetail(BaseModel):
    product_id: int
    name: str
    slug: str
    price: float
    quantity: int
    total: float
    image: Optional[str] = None

class CartCalculateOut(BaseModel):
    items: List[CartItemDetail]
    subtotal: float
    discount: float
    final_total: float
    total_count: int


# Checkout & Razorpay
class CheckoutCreateIn(BaseModel):
    full_name: str
    email: EmailStr
    billing_address: str
    items: List[CartItemIn]
    coupon_code: Optional[str] = None

class CheckoutCreateOut(BaseModel):
    order_code: str
    total_amount: float
    razorpay_order_id: str
    razorpay_key_id: str
    currency: str = "INR"

class PaymentVerifyIn(BaseModel):
    order_code: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentVerifyOut(BaseModel):
    success: bool
    message: str
    order_code: str
    download_urls: List[str] = []


# Newsletter
class NewsletterSubscribeIn(BaseModel):
    email: EmailStr

class NewsletterResponse(BaseModel):
    success: bool
    message: str


# Support Contact Ticket
class ContactMessageIn(BaseModel):
    full_name: str
    email: EmailStr
    category: Optional[str] = "general"
    subject: str
    message: str

class ContactMessageOut(BaseModel):
    ticket_id: str
    status: str
    message: str

