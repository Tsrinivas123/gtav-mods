from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models import Category, Product
from ..schemas import CategoryOut

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    """Retrieve all active categories with product count."""
    categories = db.query(Category).filter(Category.status == "active").order_by(Category.display_order).all()
    result = []
    for cat in categories:
        count = db.query(func.count(Product.id)).filter(
            Product.category_id == cat.id,
            Product.stock_status == "available",
            Product.is_deleted == False
        ).scalar()
        result.append(CategoryOut(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            icon=cat.icon or "fa-cube",
            description=cat.description or "",
            product_count=count or 0
        ))
    return result

@router.get("/{slug}", response_model=CategoryOut)
def get_category_by_slug(slug: str, db: Session = Depends(get_db)):
    """Retrieve a single category by slug."""
    cat = db.query(Category).filter(Category.slug == slug, Category.status == "active").first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    count = db.query(func.count(Product.id)).filter(
        Product.category_id == cat.id,
        Product.stock_status == "available",
        Product.is_deleted == False
    ).scalar()
    return CategoryOut(
        id=cat.id,
        name=cat.name,
        slug=cat.slug,
        icon=cat.icon or "fa-cube",
        description=cat.description or "",
        product_count=count or 0
    )

