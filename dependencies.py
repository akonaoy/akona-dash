import sys
from getpass import getpass
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models.contract import Base, User
from passlib.context import CryptContext

# Security Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def create_user():
    print("--- 👤 Create New User ---")
    
    # 1. Get Username
    username = input("Enter Username: ").strip()
    if not username:
        print("❌ Username cannot be empty.")
        return

    # 2. Get Password (Securely - characters won't show)
    password = getpass("Enter Password: ")
    confirm_password = getpass("Confirm Password: ")

    if password != confirm_password:
        print("❌ Passwords do not match!")
        return

    # 3. Get Role
    print("\nSelect Role:")
    print("1. Admin (Full Access)")
    print("2. Staff (View Only)")
    print("3. Company (Form Access)")
    role_choice = input("Choice (1-3): ").strip()

    role_map = {"1": "admin", "2": "staff", "3": "company"}
    role = role_map.get(role_choice, "staff") # Default to staff if invalid

    # 4. Save to DB
    db = SessionLocal()
    try:
        # Check if exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return

        hashed_pw = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed_pw, role=role)
        
        db.add(new_user)
        db.commit()
        print(f"\n✅ SUCCESS: User '{username}' created with role '{role}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure tables exist
    print("Checking database...")
    Base.metadata.create_all(bind=engine)
    create_user()