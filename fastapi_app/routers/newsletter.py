from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import NewsletterSubscriber
from ..schemas import NewsletterSubscribeIn, NewsletterResponse

router = APIRouter(prefix="/api/v1/newsletter", tags=["Newsletter"])

@router.post("/subscribe", response_model=NewsletterResponse)
def subscribe_newsletter(data: NewsletterSubscribeIn, db: Session = Depends(get_db)):
    """Subscribe email to PawanMod weekly giveaways and discounts."""
    normalized_email = data.email.lower().strip()

    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == normalized_email
    ).first()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            return NewsletterResponse(
                success=True,
                message="Welcome back! Your newsletter subscription has been reactivated."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email address is already subscribed."
            )

    new_sub = NewsletterSubscriber(email=normalized_email)
    db.add(new_sub)
    db.commit()

    return NewsletterResponse(
        success=True,
        message="Thank you for subscribing to PawanMod newsletter!"
    )

