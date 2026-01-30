from argon2 import PasswordHasher, exceptions
from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException

# Own imports
from ..repositories.user_repository import UserRepository
from ..utils.email_sender import send_otp_email
from ..utils.refer_id_gen import generate_referral_id
from ..utils.otp_gen import generate_otp
from ..utils.username_gen import generate_unique_username
from ..utils.jwt_utils import create_auth_token, create_refresh_token

ph = PasswordHasher()


# -----------------------------
# ✅ SIGNUP SERVICE
# -----------------------------
async def signup_user(user):
    # 1️⃣ Check if email exists
    if UserRepository.get_user_by_email(user.user_email):
        raise ValueError("Email already exists")

    # 2️⃣ Prepare user data
    user_id = str(uuid.uuid4())
    otp = generate_otp()
    user_name = generate_unique_username()

    user_data = {
        "user_id": user_id,
        "user_email": user.user_email,
        "user_name": user_name,
        "password": ph.hash(user.password),
        "otp": otp,
        "otp_expiry": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        "verified": False,
        "created_at": datetime.utcnow().isoformat(),
        "modified_at": datetime.utcnow().isoformat(),
        "refer_id": generate_referral_id()
    }

    # 3️⃣ Save user
    UserRepository.create_user(user_data)

    # 4️⃣ Send OTP email
    try:
        await send_otp_email(user.user_email, otp)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to send OTP")

    return {
        "message": "Signup successful. Verify OTP.",
        "email": user.user_email
    }


# -----------------------------
# ✅ LOGIN SERVICE
# -----------------------------
async def login_user(payload):
    # 1️⃣ Fetch user by email
    user_data = UserRepository.get_user_by_credential(payload.user_email)
    if not user_data:
        return {"success": False, "status_code": 400, "message": "User not found"}

    user = user_data[0]
    hashed_pass = user.get("password")
    verified = user.get("verified")
    user_id = user.get("user_id")

    # 2️⃣ Verify password
    try:
        ph.verify(hashed_pass, payload.password)
    except exceptions.VerifyMismatchError:
        return {"success": False, "status_code": 400, "message": "Invalid email or password"}
    except Exception:
        return {"success": False, "status_code": 500, "message": "Password verification failed"}

    # 3️⃣ Verified check
    if not verified:
        return {"success": False, "status_code": 403, "message": "Email not verified"}

    # 4️⃣ Update last_sign_in
    try:
        UserRepository.update_last_sign_in(user_id)
    except:
        return {"success": False, "status_code": 500, "message": "Failed to update last sign-in"}

    # 5️⃣ Generate tokens
    try:
        auth_token = create_auth_token(user_id)
        refresh_token = create_refresh_token(user_id)
    except:
        return {"success": False, "status_code": 500, "message": "Token generation failed"}

    # 6️⃣ Success
    return {
        "success": True,
        "status_code": 200,
        "message": "Login successful",
        "auth_token": auth_token,
        "refresh_token": refresh_token
    }
