from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session, joinedload
import time

from database import SessionLocal
from models.contract import MeetingMinute, User
from services.pdf_service import create_poytakirja_pdf
from services.storage_service import upload_file  # <-- NEW: Import the upload function
from dependencies import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

class MinuteData(BaseModel):
    organization: str
    y_tunnus: str           
    meeting_name: str
    doc_number: Optional[str] = "" 
    date: str
    time: str
    location: str
    opening_time: Optional[str] = ""
    present: str
    absent: Optional[str] = ""
    
    puheenjohtaja: str
    sihteeri: str
    tarkastaja: str
    aantenlaskija: str

    shareholders: List[Dict[str, str]] = []
    
    notice_type: Optional[str] = "standard"
    notice_custom: Optional[str] = ""
    declarations_type: Optional[str] = "standard"
    declarations_custom: Optional[str] = ""
    
    # NEW: Sections 6 to 12 Fields
    new_company_name: Optional[str] = ""
    board_member: Optional[str] = ""
    board_deputy: Optional[str] = ""
    ceo: Optional[str] = ""
    financial_year_end: Optional[str] = ""
    domicile: Optional[str] = ""          
    business_lines: Optional[str] = ""    

    # MISSING FIELDS ADDED HERE:
    redemption_right: Optional[str] = ""
    bank_details: Optional[str] = ""

    agenda_items: List[Dict[str, str]] = []
    closing_time: Optional[str] = ""
    name_puheenjohtaja: Optional[str] = ""
    role_puheenjohtaja: Optional[str] = "toimitusjohtaja" 
    name_sihteeri: Optional[str] = ""
    role_sihteeri: Optional[str] = "varajäsen"            
    sig_puheenjohtaja: Optional[str] = ""
    sig_sihteeri: Optional[str] = ""

@router.post("/")
async def create_minute(data: MinuteData, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Generate PDF locally
    local_pdf_path = create_poytakirja_pdf(data.dict())
    
    # 2. Upload to Supabase Storage -> inside the "minutes" folder!
    public_pdf_url = upload_file(local_pdf_path, folder="minutes")

    # 3. Save to database using the cloud URL
    new_minute = MeetingMinute(
        organization=data.organization,
        meeting_name=data.meeting_name,
        date=data.date,
        pdf_url=public_pdf_url,  # <-- NEW: Save the Supabase URL instead of local path
        created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        user_id=current_user.id
    )
    db.add(new_minute)
    db.commit()
    
    return {"status": "success", "pdf": public_pdf_url}  # <-- NEW: Return cloud link to frontend

@router.get("/list")
async def list_minutes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role in ["admin", "staff"]:
        minutes = db.query(MeetingMinute).options(joinedload(MeetingMinute.user)).all()
    else:
        minutes = db.query(MeetingMinute).filter(MeetingMinute.user_id == current_user.id).options(joinedload(MeetingMinute.user)).all()

    results = []
    for m in minutes:
        results.append({
            "id": m.id, "created_at": m.created_at, "organization": m.organization,
            "meeting_name": m.meeting_name, "date": m.date, "pdf_url": m.pdf_url,
            "created_by": m.user.username if m.user else "Unknown"
        })
    return results