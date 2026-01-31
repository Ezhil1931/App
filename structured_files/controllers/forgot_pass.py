from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import random

from argon2 import PasswordHasher

from ..config.supabase_config import supabase
from ..utils.email_sender import send_otp_email


router = APIRouter()
ph = PasswordHasher()



class ForgotPasswordRequest(BaseModel):
    identifier: str  


@router.post("/forgot-password/request")
async def forgot_password_request(payload: ForgotPasswordRequest):

    identifier = payload.identifier.strip()




    res = (
        supabase.table("users")
        .select("user_id, user_name, user_email")
        .or_(
            f"user_email.ilike.{identifier},"
            f"user_name.ilike.{identifier}"
        )
        .limit(1)
        .execute()
    )

    # 🔐 Always return success (anti-enumeration)
    
    if not res.data:
        return {
            "status": 200,
            "message": "If account exists, OTP has been sent"
        }


    user = res.data[0]


    otp = str(random.randint(100000, 999999))
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

    supabase.table("users").update({
        "otp": otp,
        "otp_expiry": otp_expiry.isoformat(),
        "modified_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user["user_id"]).execute()

    try:
        await send_otp_email(
            "user",
            user["user_email"],
            otp
        )
    except Exception:
     
        pass

    return {
        "status": 200,
        "message": "If account exists, OTP has been sent"
    }

#---------------verififng the otp for password change----------------------

class ForgotPasswordVerify(BaseModel):
    identifier: str   
    otp: str
    new_password: str


@router.post("/forgot-password/verify")
async def forgot_password_verify(payload: ForgotPasswordVerify):

    identifier = payload.identifier.strip()

    res = (
        supabase.table("users")
        .select("user_id, otp, otp_expiry")
        .or_(
            f"user_email.ilike.{identifier},"
            f"user_name.ilike.{identifier}"
        )
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=400, detail="Invalid request")

    user = res.data[0]

    # OTP existence check
    if not user.get("otp") or not user.get("otp_expiry"):
        raise HTTPException(status_code=400, detail="OTP not requested")

    # Expiry check FIRST
    otp_expiry = datetime.fromisoformat(
        user["otp_expiry"].replace("Z", "+00:00")
    )

    if datetime.now(timezone.utc) > otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    # OTP comparison
    if user["otp"] != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Hash new password
    hashed_password = ph.hash(payload.new_password)

    supabase.table("users").update({
        "password": hashed_password,
        "otp": None,
        "otp_expiry": None,
        "modified_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user["user_id"]).execute()

    return {
        "status": 200,
        "message": "Password reset successful"
    }
