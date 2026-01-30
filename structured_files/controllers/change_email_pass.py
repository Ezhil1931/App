from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import random
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard
from ..utils.email_sender import send_otp_email

router = APIRouter()
ph = PasswordHasher()


class RequestEmailChange(BaseModel):
    new_email: EmailStr
    current_password: str


@router.post("/change-email/request")
async def request_email_change(
    payload: RequestEmailChange,
    user=Depends(auth_guard)
):
    user_id = user["user_id"]

    # 1️⃣ Check if email already exists
    email_check = (
        supabase.table("users")
        .select("user_id")
        .eq("user_email", payload.new_email)
        .limit(1)
        .execute()
    )

    if email_check.data:
        raise HTTPException(status_code=409, detail="Email already in use")

    # 2️⃣ Fetch current password + name
    res = (
        supabase.table("users")
        .select("password, user_name")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")

    user_row = res.data[0]

    # 3️⃣ Verify password
    try:
        ph.verify(user_row["password"], payload.current_password)
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid password")

    # 4️⃣ Generate OTP
    otp = str(random.randint(100000, 999999))
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

    # 5️⃣ Store OTP ONLY
    supabase.table("users").update({
        "otp": otp,
        "otp_expiry": otp_expiry.isoformat(),
        "modified_at": datetime.now(timezone.utc).isoformat(),
        "modified_by": user_id
    }).eq("user_id", user_id).execute()

    # 6️⃣ Send OTP to NEW email
    try:
        await send_otp_email(
           "user",
            payload.new_email,
           otp
        )
    except Exception:
        # rollback OTP
        supabase.table("users").update({
            "otp": None,
            "otp_expiry": None
        }).eq("user_id", user_id).execute()

        raise HTTPException(status_code=502, detail="Failed to send OTP email")

    return {
        "status": 200,
        "message": "OTP sent to new email"
    }



#-------------verifying the otp and update email-------------
class VerifyEmailChange(BaseModel):
    new_email: EmailStr
    otp: str


@router.post("/change-email/verify")
async def verify_email_change(
    payload: VerifyEmailChange,
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

    user_row = res.data[0]

    # 2️⃣ Expiry check
    otp_expiry = datetime.fromisoformat(
        user_row["otp_expiry"].replace("Z", "+00:00")
    )

    if datetime.now(timezone.utc) > otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    # 3️⃣ Verify OTP
    if user_row["otp"] != payload.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")

    # 4️⃣ Update email + clear OTP
    supabase.table("users").update({
        "user_email": payload.new_email,
        "otp": None,
        "otp_expiry": None,
        "modified_at": datetime.now(timezone.utc).isoformat(),
        "modified_by": user_id
    }).eq("user_id", user_id).execute()

    return {
        "status": 200,
        "message": "Email updated successfully"
    }
