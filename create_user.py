import os
from dotenv import load_dotenv
from pathlib import Path

# Force loading from backend/.env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Load variables securely
DATABASE_URL = os.getenv("DATABASE_URL")
SENDGRID_KEY = os.getenv("SENDGRID_KEY")

# Supabase Storage Variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "documents")