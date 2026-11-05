import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")

# Data Directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RAW_INSTACART_DIR = RAW_DATA_DIR / "instacart"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
APPLICATION_DATA_DIR = DATA_DIR / "application"

# Application Data Files (LuxStore)
PRODUCTS_FILE = APPLICATION_DATA_DIR / "products.csv"
TRANSACTIONS_FILE = APPLICATION_DATA_DIR / "transactions.csv"
USERS_FILE = APPLICATION_DATA_DIR / "users.json"

# Logging and Artifact Directories
LOGS_DIR = BASE_DIR / "logs"
DEV_OTP_LOG_FILE = LOGS_DIR / "otp_dev_log.json"
SAVED_MODELS_DIR = BASE_DIR / "ml" / "saved_models"

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
APPLICATION_DATA_DIR.mkdir(parents=True, exist_ok=True)
SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    """Central Application Configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "luxstore-ml-secure-key-2026")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1")
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "127.0.0.1")
    
    # Paths
    BASE_DIR = BASE_DIR
    PRODUCTS_FILE = PRODUCTS_FILE
    TRANSACTIONS_FILE = TRANSACTIONS_FILE
    USERS_FILE = USERS_FILE
    LOGS_DIR = LOGS_DIR
    SAVED_MODELS_DIR = SAVED_MODELS_DIR
    DEV_OTP_LOG_FILE = DEV_OTP_LOG_FILE
    
    # Microservices
    NODE_EMAIL_SCRIPT = BASE_DIR / "email_service.js"

