from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import ContactMessage
from ..schemas import ContactMessageIn, ContactMessageOut

router = APIRouter(prefix="/api/v1/contact", tags=["Support & Contact"])

@router.post("", response_model=ContactMessageOut)
def submit_contact_ticket(data: ContactMessageIn, request: Request, db: Session = Depends(get_db)):
    """Submit a support ticket to PawanMod moderators."""
    count = db.query(func.count(ContactMessage.id)).scalar() or 0
    ticket_id = f"PM-{count + 1:06d}"

    client_ip = request.client.host if request.client else "127.0.0.1"

    new_msg = ContactMessage(
        ticket_id=ticket_id,
        full_name=data.full_name,
        email=data.email,
        category=data.category or "general",
        subject=data.subject,
        message=data.message,
        ip_address=client_ip,
        status="open"
    )
    db.add(new_msg)
    db.commit()

    return ContactMessageOut(
        ticket_id=ticket_id,
        status="open",
        message="Your support ticket has been submitted. Our moderators will reply shortly."
    )

