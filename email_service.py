from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import time
import os 

from database import SessionLocal
from models.contract import Contract, User
from services.pdf_service import create_pdf
from services.email_service import send_email
from dependencies import get_current_user 

# NEW: Import your Supabase upload function!
from services.storage_service import upload_file 

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ContractData(BaseModel):
    sector: str
    employer_name: str
    employer_y_tunnus: str
    employer_address: str
    employer_phone: str
    employer_email: str
    employer_yhteyshenkilo: Optional[str] = ""
    employer_asema: str
    employee_firstname: str
    employee_lastname: str
    employee_hetu: str
    employee_address: str
    employee_phone: str
    employee_email: str
    employee_veronumero: str
    employee_tilinumero: str
    start_date: str
    contract_type: str
    end_date: Optional[str] = ""
    koeaika: str
    job_title: str
    tyopaikka: str
    tyoaika_tyyppi: str
    tyoaika_tarkenne: Optional[str] = ""
    palkka_tyyppi: str
    palkka_tarkenne: Optional[str] = ""
    palkanmaksupaiva: str
    muut_ehdot: Optional[str] = ""
    employer_signature: str
    employee_signature: str

@router.post("/")
async def create_contract(data: ContractData, 
                          background_tasks: BackgroundTasks, 
                          db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)
                          ):
    # 1. Generate PDF locally
    local_pdf_path = create_pdf(data.dict())

    # 2. Upload to Supabase Storage -> inside the "contracts" folder!
    public_pdf_url = upload_file(local_pdf_path, folder="contracts")

    # 3. Save Metadata to Database with User ID
    new_contract = Contract(
        sector=data.sector,
        employer_name=data.employer_name,
        employer_email=data.employer_email,
        employee_firstname=data.employee_firstname,
        employee_lastname=data.employee_lastname,
        employee_email=data.employee_email,
        start_date=data.start_date,
        job_title=data.job_title,
        salary_info=data.palkka_tyyppi,
        pdf_url=public_pdf_url,  # <--- UPDATED: Saves the Supabase cloud link!
        created_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        user_id=current_user.id
    )
    db.add(new_contract)
    db.commit()

    # 4. Email Content
    subject = f"Allekirjoitettu työsopimus: {data.employer_name} - {data.employee_lastname}"
    body = f"""
    Hei,

    Uusi työsopimus on allekirjoitettu.
    Löydät sopimuksen tämän viestin liitteenä (PDF). Voit myös ladata sen tästä linkistä:
    {public_pdf_url}

    Työnantaja: {data.employer_name}
    Työntekijä: {data.employee_firstname} {data.employee_lastname}
    """

    # 5. Send Emails (Using local_pdf_path so SendGrid can attach it!)
    background_tasks.add_task(send_email, data.employer_email, subject, body, local_pdf_path)
    background_tasks.add_task(send_email, data.employee_email, subject, body, local_pdf_path)

    admin_email = os.getenv("SENDER_EMAIL") 
    if admin_email:
        background_tasks.add_task(send_email, admin_email, f"ADMIN COPY: {subject}", body, local_pdf_path)

    # UPDATED: Returns the public URL to the frontend
    return {"status": "success", "pdf": public_pdf_url}