from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="staff")
    
    # Link user to their contracts
    contracts = relationship("Contract", back_populates="user")

    meeting_minutes = relationship("MeetingMinute", back_populates="user")

class MeetingMinute(Base):
    __tablename__ = "meeting_minutes"

    id = Column(Integer, primary_key=True)
    organization = Column(String)
    meeting_name = Column(String)
    date = Column(String)
    created_at = Column(String)
    pdf_url = Column(String)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="meeting_minutes")

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    
    # Meta
    sector = Column(String)
    created_at = Column(String)
    
    # Employer
    employer_name = Column(String)
    employer_email = Column(String)
    
    # Employee
    employee_firstname = Column(String)
    employee_lastname = Column(String)
    employee_email = Column(String)
    
    # Contract Details
    start_date = Column(String)
    job_title = Column(String)
    salary_info = Column(String)
    
    # Files
    pdf_url = Column(String)  # AWS S3 Link
    
    # Status
    signed = Column(Boolean, default=True)

    # NEW: Link to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="contracts")