from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from ..database import get_db
from ..models import Product, Category, Review
from ..schemas import ProductListItem, ProductDetailOut, ReviewOut

router = APIRouter(prefix="/api/v1/products", tags=["Products"])

def calculate_discount(price, old_price):
    if old_price and old_price > price:
        return int(round(((old_price - price) / old_price) * 100))
    return 0

@router.get("", response_model=List[ProductListItem])
def list_products(
    search: Optional[str] = Query(None, description="Search by name, description, or category"),
    category: Optional[str] = Query(None, description="Filter by category slug"),
    is_featured: Optional[bool] = Query(None),
    is_trending: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("newest", pattern="^(newest|popular|price_low|price_high)$"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve catalog products with rich filtering, search, and sorting."""
    query = db.query(Product).join(Category).filter(
        Product.stock_status == "available",
        Product.is_deleted == False,
        Category.status == "active"
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(s),
                Product.short_description.ilike(s),
                Product.description.ilike(s),
                Category.name.ilike(s)
            )
        )

    if category:
        slug_aliases = {
            "maps": "maps-safehouses",
            "scripts": "scripts-huds",
            "graphics": "graphics-presets"
        }
        resolved_category = slug_aliases.get(category, category)
        query = query.filter(Category.slug == resolved_category)

    if is_featured is not None:
        query = query.filter(Product.is_featured == is_featured)

    if is_trending is not None:
        query = query.filter(Product.is_trending == is_trending)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort_by == "newest":
        query = query.order_by(Product.created_at.desc())
    elif sort_by == "popular":
        query = query.order_by(Product.downloads_count.desc())
    elif sort_by == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_high":
        query = query.order_by(Product.price.desc())

    products = query.offset(offset).limit(limit).all()

    return [
        ProductListItem(
            id=p.id,
            name=p.name,
            slug=p.slug,
            short_description=p.short_description or "",
            price=float(p.price),
            old_price=float(p.old_price) if p.old_price else None,
            discount_percentage=calculate_discount(float(p.price), float(p.old_price) if p.old_price else None),
            main_image=p.main_image,
            downloads_count=p.downloads_count,
            stock_status=p.stock_status,
            is_featured=p.is_featured,
            is_trending=p.is_trending,
            category_slug=p.category.slug if p.category else None,
            category_name=p.category.name if p.category else None
        )
        for p in products
    ]

@router.get("/{slug}", response_model=ProductDetailOut)
def get_product_detail(slug: str, db: Session = Depends(get_db)):
    """Retrieve full product detail by slug with reviews and specifications."""
    product = db.query(Product).join(Category).filter(
        Product.slug == slug,
        Product.stock_status == "available",
        Product.is_deleted == False,
        Category.status == "active"
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = db.query(Review).filter(Review.product_id == product.id).order_by(Review.created_at.desc()).all()
    avg_rating = db.query(func.avg(Review.rating)).filter(Review.product_id == product.id).scalar()

    return ProductDetailOut(
        id=product.id,
        name=product.name,
        slug=product.slug,
        short_description=product.short_description or "",
        description=product.description or "",
        requirements=product.requirements or "",
        installation_guide=product.installation_guide or "",
        price=float(product.price),
        old_price=float(product.old_price) if product.old_price else None,
        discount_percentage=calculate_discount(float(product.price), float(product.old_price) if product.old_price else None),
        main_image=product.main_image,
        downloads_count=product.downloads_count,
        stock_status=product.stock_status,
        is_featured=product.is_featured,
        is_trending=product.is_trending,
        category_slug=product.category.slug if product.category else None,
        category_name=product.category.name if product.category else None,
        reviews=[
            ReviewOut(
                id=r.id,
                reviewer_name=r.reviewer_name,
                rating=r.rating,
                title=r.title or "",
                content=r.content or "",
                created_at=r.created_at
            )
            for r in reviews
        ],
        average_rating=round(float(avg_rating), 1) if avg_rating else None,
        reviews_count=len(reviews)
    )
