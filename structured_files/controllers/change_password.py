from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import random

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard
from ..utils.email_sender import send_otp_email

router = APIRouter()
ph = PasswordHasher()


class RequestPasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password/request")
async def request_password_change(
    payload: RequestPasswordChange,
    user=Depends(auth_guard)
):
    user_id = user["user_id"]

    # 1️⃣ Fetch user data
    res = (
        supabase.table("users")
        .select("password, user_name, user_email")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    user_row = res.data[0]

    # 2️⃣ Verify current password
    try:
        ph.verify(user_row["password"], payload.current_password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid current password")

    # 3️⃣ Generate OTP
    otp = str(random.randint(100000, 999999))
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

   

    # 5️⃣ Store OTP + pending password
    supabase.table("users").update({
        "otp": otp,
        "otp_expiry": otp_expiry.isoformat(),
      
        "modified_at": datetime.now(timezone.utc).isoformat(),
        "modified_by": user_id
    }).eq("user_id", user_id).execute()

    # 6️⃣ Send OTP to registered email
    try:
        await send_otp_email(
         "user",
            user_row["user_email"],
            otp
        )
    except Exception:
        # rollback on email failure
        supabase.table("users").update({
            "otp": None,
            "otp_expiry": None,
        }).eq("user_id", user_id).execute()

        raise HTTPException(status_code=502, detail="Failed to send OTP")

    return {
        "status": 200,
        "message": "OTP sent to registered email"
    }



#-------------verify otp and update the password 

class VerifyPasswordOTP(BaseModel):
    otp: str
    new_password: str
from datetime import datetime, timezone

@router.post("/change-password/verify")
async def verify_password_change(
    payload: VerifyPasswordOTP,
    user=Depends(auth_guard)
):
    user_id = user["user_id"]

    # 1️⃣ Fetch OTP
    res = (
        supabase.table("users")
        .select("otp, otp_expiry")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not res.data or not res.data[0].get("otp"):
        raise HTTPException(status_code=400, detail="OTP not found")

    row = res.data[0]

    # 2️⃣ Expiry check
    otp_expiry_str = row["otp_expiry"]

    # Supabase ISO string example: '2026-01-31T02:20:54.981460+00:00'
    # Normalize to 6-digit microseconds if needed
    if "." in otp_expiry_str:
        date_part, rest = otp_expiry_str.split(".")
        micro = rest[:6].ljust(6, "0")
        tz = rest[6:]
        otp_expiry_str = f"{date_part}.{micro}{tz}"

    otp_expiry = datetime.fromisoformat(otp_expiry_str)

    if datetime.now(timezone.utc) > otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    # 3️⃣ Verify OTP
    if row["otp"] != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    # 4️⃣ Hash new password AFTER OTP verification
    new_hashed_password = ph.hash(payload.new_password)

    # 5️⃣ Update password + cleanup
    supabase.table("users").update({
        "password": new_hashed_password,
        "otp": None,
        "otp_expiry": None,
        "modified_at": datetime.now(timezone.utc).isoformat(),
        "modified_by": user_id
    }).eq("user_id", user_id).execute()

    return {
        "status": 200,
        "message": "Password updated successfully"
    }
