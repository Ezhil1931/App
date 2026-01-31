from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import random

from ..config.supabase_config import supabase
from ..utils.email_sender import send_otp_email

router = APIRouter()


# ------------------ Payload ------------------
class OTPResendPayload(BaseModel):
    user_email: EmailStr


# ------------------ Utils ------------------
def generate_otp() -> str:
    return str(random.randint(100000, 999999))


# ------------------ Route ------------------
@router.post("/otp/resend")
async def resend_otp(payload: OTPResendPayload):

   
    user_resp = (
        supabase.table("users")
        .select("user_id, user_name, user_email, verified")
        .eq("user_email", payload.user_email)
        .limit(1)
        .execute()
    )

    if not user_resp.data:
        raise HTTPException(status_code=404, detail="User not found")

    user = user_resp.data[0]   

    

    # 2️⃣ Generate OTP
    otp = generate_otp()
    otp_expiry = datetime.utcnow() + timedelta(minutes=10)

    # 3️⃣ Update user record
    supabase.table("users").update({
        "otp": otp,
        "otp_expiry": otp_expiry.isoformat()
    }).eq("user_id", user["user_id"]).execute() 

    # 4️⃣ Send OTP email
    try:
        await send_otp_email(user["user_name"],user["user_email"],otp)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send OTP: {str(e)}"
        )

    return {
        "status": 200,
        "message": "OTP resent successfully"
        
    }
