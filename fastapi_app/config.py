import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration (Auto-detects DATABASE_URL or falls back to local SQLite)
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if RAW_DATABASE_URL:
    # Handle postgres:// vs postgresql:// for SQLAlchemy
    if RAW_DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif RAW_DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = RAW_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        DATABASE_URL = RAW_DATABASE_URL
else:
    SQLITE_PATH = BASE_DIR / "db.sqlite3"
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"

# App Config
SECRET_KEY = os.getenv("SECRET_KEY", "fastapi-pawanmod-secret-key-2026")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Razorpay Config
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_pawanmod")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "pawanmod_secret")

# Allowed CORS Origins
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "https://gtav-mods.vercel.app",
    "*"
]

