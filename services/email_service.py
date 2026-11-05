"""
Email & OTP Microservice interface for Relate (LuxStore).
Integrates with the Node.js Nodemailer service and manages secure in-memory OTP sessions.
"""

import subprocess
import time
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from config.config import Config

# In-memory OTP session store: { email: { otp_hash, expires_at, attempts, verified, last_sent } }
_otp_store = {}


def generate_secure_otp() -> str:
    """Generate a cryptographically secure 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000:06d}"


def request_password_reset_otp(email: str, user_name: str = "Valued Customer") -> dict:
    """
    Generate an OTP and dispatch it via the Node.js Nodemailer microservice.
    Enforces a 60-second resend cooldown and 5-minute expiration.
    """
    email_clean = email.strip().lower()
    now = time.time()
    
    # Check resend cooldown
    existing = _otp_store.get(email_clean)
    if existing and (now - existing.get('last_sent', 0)) < 60:
        remaining_cd = int(60 - (now - existing['last_sent']))
        return {
            "success": False,
            "error": f"Please wait {remaining_cd} seconds before requesting a new code.",
            "status_code": 429
        }
        
    otp_code = generate_secure_otp()
    otp_hash = generate_password_hash(otp_code)
    
    _otp_store[email_clean] = {
        "otp_hash": otp_hash,
        "expires_at": now + 300,  # 5 minutes validity
        "attempts": 0,
        "verified": False,
        "last_sent": now
    }
    
    # Dispatch via Node.js microservice
    try:
        cmd = ['node', str(Config.NODE_EMAIL_SCRIPT), email_clean, otp_code, user_name]
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(Config.BASE_DIR)
        )
    except Exception as e:
        print(f"Subprocess error invoking email_service.js: {e}")
        
    return {
        "success": True,
        "message": "If an account is associated with that email, a 6-digit verification code has been dispatched."
    }


def verify_password_reset_otp(email: str, otp_code: str) -> dict:
    """
    Verify the entered OTP against the securely stored hash.
    Enforces 5-attempt ceiling and expiration checks.
    """
    email_clean = email.strip().lower()
    otp_clean = otp_code.strip()
    
    if not email_clean or not otp_clean:
        return {"success": False, "error": "Email and verification code are required.", "status_code": 400}
        
    record = _otp_store.get(email_clean)
    if not record:
        return {"success": False, "error": "No reset request found for this email. Please request a new code.", "status_code": 400}
        
    now = time.time()
    if now > record['expires_at']:
        del _otp_store[email_clean]
        return {"success": False, "error": "The verification code has expired. Please request a new one.", "status_code": 400}
        
    if record['attempts'] >= 5:
        del _otp_store[email_clean]
        return {"success": False, "error": "Maximum verification attempts exceeded. Please request a new code.", "status_code": 429}
        
    record['attempts'] += 1
    
    if not check_password_hash(record['otp_hash'], otp_clean):
        remaining = 5 - record['attempts']
        return {"success": False, "error": f"Invalid verification code. {remaining} attempt(s) remaining.", "status_code": 400}
        
    record['verified'] = True
    return {"success": True, "message": "Code verified successfully. You may now enter your new password."}


def is_otp_verified(email: str) -> bool:
    """Check if the email has successfully passed OTP verification."""
    email_clean = email.strip().lower()
    record = _otp_store.get(email_clean)
    return bool(record and record.get('verified'))


def consume_verified_otp(email: str) -> None:
    """Invalidate OTP session after successful password reset."""
    email_clean = email.strip().lower()
    if email_clean in _otp_store:
        del _otp_store[email_clean]

