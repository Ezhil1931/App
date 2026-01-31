# app/routes/otp_verification.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from ..config.supabase_config import supabase

router = APIRouter()


class OTPVerifyPayload(BaseModel):
    user_email: EmailStr
    otp: str


@router.post("/otp/verify", status_code=status.HTTP_200_OK)
async def verify_otp(payload: OTPVerifyPayload):

    # 1️⃣ Fetch user INCLUDING otp fields
    user_resp = (
        supabase.table("users")
        .select(
            "user_id, user_name, user_email, verified, otp, otp_expiry"
        )
        .eq("user_email", payload.user_email)
        .limit(1)
        .execute()
    )

    if not user_resp.data:
        raise HTTPException(status_code=404, detail="User not found")

    user = user_resp.data[0]

    # 2️⃣ Check OTP existence
    if not user.get("otp") or not user.get("otp_expiry"):
        raise HTTPException(status_code=400, detail="OTP not requested")

    # 3️⃣ Check expiry
    otp_expiry = datetime.fromisoformat(
        user["otp_expiry"].replace("Z", "+00:00")
    )

    if datetime.now(timezone.utc) > otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired")

    # 4️⃣ Check OTP
    if user["otp"] != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # 5️⃣ Mark verified & clear OTP
    supabase.table("users").update({
        "verified": True,
        "otp": None,
        "otp_expiry": None,
        "modified_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user["user_id"]).execute()

    return {
    "status": 200,
    "message": "OTP verified successfully"
}
