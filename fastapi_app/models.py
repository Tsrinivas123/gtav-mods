from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Category(Base):
    __tablename__ = "marketplace_category"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    icon = Column(String(50), default="fa-cube")
    image = Column(String(100), nullable=True)
    description = Column(Text, default="")
    status = Column(String(20), default="active")
    display_order = Column(Integer, default=0)
    seo_title = Column(String(200), default="")
    meta_description = Column(Text, default="")
    meta_keywords = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "marketplace_product"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    short_description = Column(String(255), default="")
    description = Column(Text, default="")
    requirements = Column(Text, default="")
    installation_guide = Column(Text, default="")
    price = Column(Numeric(10, 2), nullable=False)
    old_price = Column(Numeric(10, 2), nullable=True)
    downloads_count = Column(Integer, default=0)
    stock_status = Column(String(20), default="available")
    is_featured = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    main_image = Column(String(100), nullable=True)
    category_id = Column(Integer, ForeignKey("marketplace_category.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    reviews = relationship("Review", back_populates="product")


class Review(Base):
    __tablename__ = "marketplace_review"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_name = Column(String(100), default="Anonymous")
    rating = Column(Integer, default=5)
    title = Column(String(150), default="")
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    product_id = Column(Integer, ForeignKey("marketplace_product.id"), nullable=False)

    product = relationship("Product", back_populates="reviews")


class NewsletterSubscriber(Base):
    __tablename__ = "marketplace_newslettersubscriber"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class ContactMessage(Base):
    __tablename__ = "marketplace_contactmessage"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    email = Column(String(254), nullable=False)
    category = Column(String(50), default="general")
    subject = Column(String(255), default="")
    message = Column(Text, nullable=False)
    ip_address = Column(String(39), nullable=True)
    status = Column(String(20), default="open")
    is_read = Column(Boolean, default=False)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders_order"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(254), nullable=False)
    billing_address = Column(Text, default="")
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0.0)
    payment_method = Column(String(50), default="razorpay")
    payment_id = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")
    payment_status = Column(String(20), default="Pending")
    invoice_number = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "orders_orderitem"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders_order.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("marketplace_product.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

