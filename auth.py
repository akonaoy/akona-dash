from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from datetime import timedelta
from pydantic import BaseModel
from typing import List

from database import SessionLocal
from models.contract import User, Contract
from services.auth import verify_password, create_access_token, get_password_hash
from dependencies import get_current_user, require_admin

router = APIRouter()

class UserCreateSchema(BaseModel):
    username: str
    password: str
    role: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- AUTHENTICATION ---

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, 
        expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

# --- DASHBOARD ROUTES ---

@router.get("/dashboard")
async def get_dashboard_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contracts = []

    # Admin & Staff: See ALL contracts
    if current_user.role in ["admin", "staff"]:
        contracts = db.query(Contract).options(joinedload(Contract.user)).all()
    
    # Company / Trainee: See ONLY THEIR OWN contracts
    elif current_user.role == "company":
        contracts = db.query(Contract).filter(Contract.user_id == current_user.id).options(joinedload(Contract.user)).all()

    # Format the results
    results = []
    for c in contracts:
        results.append({
            "id": c.id,
            "created_at": c.created_at,
            "employer_name": c.employer_name,
            "employee_firstname": c.employee_firstname,
            "employee_lastname": c.employee_lastname,
            "sector": c.sector,
            "pdf_url": c.pdf_url,
            "created_by": c.user.username if c.user else "Unknown"
        })
    return results

# --- USER MANAGEMENT ROUTES (Admins Only) ---

@router.get("/users")
async def get_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]

@router.post("/users")
async def create_user(new_user: UserCreateSchema, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == new_user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pw = get_password_hash(new_user.password)
    db_user = User(username=new_user.username, hashed_password=hashed_pw, role=new_user.role)
    db.add(db_user)
    db.commit()
    return {"msg": "User created successfully"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself!")

    db.delete(user)
    db.commit()
    return {"msg": "User deleted"}