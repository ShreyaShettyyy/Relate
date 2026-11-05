"""
Authentication and User Profile Management Service for Relate (LuxStore).
Handles user storage, password hashing (Werkzeug), profiles, and cart/wishlist/orders persistence.
"""

import json
import time
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import USERS_FILE


def load_db(file_path: Path = USERS_FILE) -> dict:
    """Load users JSON database."""
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading user database: {e}")
        return {}


def save_db(db: dict, file_path: Path = USERS_FILE) -> None:
    """Persist users JSON database."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4)
    except Exception as e:
        print(f"Error saving user database: {e}")


def register_user(name: str, email: str, password: str) -> dict:
    """Register a new customer account."""
    name_clean = name.strip()
    email_clean = email.strip().lower()
    
    if not name_clean or not email_clean or not password:
        return {"success": False, "error": "Missing required fields.", "status_code": 400}
        
    db = load_db()
    if email_clean in db:
        return {"success": False, "error": "User with this email already exists.", "status_code": 400}
        
    hashed_password = generate_password_hash(password)
    new_cust_id = len(db) + 1101
    
    db[email_clean] = {
        "name": name_clean,
        "password": hashed_password,
        "customer_id": new_cust_id,
        "cart": [],
        "wishlist": [],
        "orders": [],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_db(db)
    
    return {
        "success": True,
        "user": {
            "email": email_clean,
            "name": name_clean,
            "customer_id": new_cust_id
        }
    }


def authenticate_user(email: str, password: str) -> dict:
    """Authenticate customer login credentials."""
    email_clean = email.strip().lower()
    
    if not email_clean or not password:
        return {"success": False, "error": "Email and password are required.", "status_code": 400}
        
    db = load_db()
    if email_clean not in db:
        return {"success": False, "error": "Invalid email or password.", "status_code": 401}
        
    user = db[email_clean]
    existing_pwd = user.get('password', '')
    
    if not (check_password_hash(existing_pwd, password) or existing_pwd == password):
        return {"success": False, "error": "Invalid email or password.", "status_code": 401}
        
    return {
        "success": True,
        "user": {
            "email": email_clean,
            "name": user['name'],
            "customer_id": user['customer_id']
        }
    }


def update_user_name(email: str, new_name: str) -> dict:
    """Update user's profile display name."""
    email_clean = email.strip().lower()
    name_clean = new_name.strip()
    
    if not name_clean:
        return {"success": False, "error": "Name cannot be empty.", "status_code": 400}
        
    db = load_db()
    if email_clean not in db:
        return {"success": False, "error": "User not found.", "status_code": 404}
        
    db[email_clean]['name'] = name_clean
    save_db(db)
    
    return {
        "success": True,
        "message": "Profile updated successfully.",
        "user": {
            "email": email_clean,
            "name": name_clean,
            "customer_id": db[email_clean]['customer_id']
        }
    }


def change_user_password(email: str, current_password: str, new_password: str) -> dict:
    """Change user password after verifying existing password."""
    email_clean = email.strip().lower()
    
    if not email_clean or not current_password or not new_password:
        return {"success": False, "error": "All password fields are required.", "status_code": 400}
        
    if len(new_password) < 4:
        return {"success": False, "error": "New password must be at least 4 characters long.", "status_code": 400}
        
    db = load_db()
    if email_clean not in db:
        return {"success": False, "error": "User not found.", "status_code": 404}
        
    user = db[email_clean]
    existing_pwd = user.get('password', '')
    
    if not (check_password_hash(existing_pwd, current_password) or existing_pwd == current_password):
        return {"success": False, "error": "Incorrect current password.", "status_code": 400}
        
    user['password'] = generate_password_hash(new_password)
    save_db(db)
    return {"success": True, "message": "Password changed successfully."}


def reset_password_with_hash(email: str, new_password: str) -> dict:
    """Reset password following successful OTP verification."""
    email_clean = email.strip().lower()
    
    if len(new_password) < 4:
        return {"success": False, "error": "Password must be at least 4 characters long.", "status_code": 400}
        
    db = load_db()
    if email_clean not in db:
        return {"success": False, "error": "Account not found.", "status_code": 404}
        
    db[email_clean]['password'] = generate_password_hash(new_password)
    save_db(db)
    return {"success": True, "message": "Your password has been reset successfully. Please log in with your new credentials."}

