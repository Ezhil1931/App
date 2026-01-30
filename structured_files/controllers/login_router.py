from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from argon2 import PasswordHasher, exceptions
from datetime import datetime, timedelta, timezone
import jwt

from ..config.supabase_config import supabase
from ..utils.rsa_keys import PRIVATE_KEY, ALGORITHM
from ..utils.jwt_utils import create_auth_token ,create_refresh_token
router = APIRouter()
ph = PasswordHasher()


# -----------------------------------------
# 📌 Login Payload
# -----------------------------------------
class LoginPayload(BaseModel):
    user_email: EmailStr
    password: str


# ----------------------------------------------------------------
# ✅ LOGIN ENDPOINT — with complete & correct error handling
# ----------------------------------------------------------------
@router.post("/login")
async def login(payload: LoginPayload):
    try:
        # 1️⃣ Fetch user by email
        resp = (
            supabase.table("users")
            .select("user_id,user_email,password,verified,last_sign_in")
            .eq("user_email",payload.user_email)
            .execute()
        )

        # No user found
        if resp.data is None or len(resp.data) == 0:
            raise HTTPException(status_code=400, detail="User not found")

        user = resp.data[0]

        user_id = user["user_id"]
        hashed_pass = user["password"]
        verified = user["verified"]

        # 2️⃣ Verify password
        try:
            ph.verify(hashed_pass, payload.password)
        except exceptions.VerifyMismatchError:
            raise HTTPException(status_code=400, detail="Invalid email or password")
        except Exception:
            raise HTTPException(status_code=500, detail="Password check failed")

        # 3️⃣ Verified check
        if not verified:
            raise HTTPException(status_code=403, detail="Email not verified")

        # 4️⃣ Update last_sign_in
        try:
            supabase.table("users").update({
                "last_sign_in": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", user_id).execute()
        except:
            raise HTTPException(status_code=500, detail="Failed to update last sign-in")

        # 5️⃣ Create tokens
        try:
            auth_token = create_auth_token(user_id)
            refresh_token = create_refresh_token(user_id)
        except:
            raise HTTPException(status_code=500, detail="Token generation failed")

        # 6️⃣ Success Response
        return {
            "status": 200,
            "message": "Login successful",
           
            "auth_token": auth_token,
            "refresh_token": refresh_token,
        }

    except HTTPException:
        raise

    except Exception as e:
        

        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )
