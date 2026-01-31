from fastapi import APIRouter, Header, HTTPException
from ..utils.jwt_utils import (
    verify_refresh_token,
    create_auth_token,
    create_refresh_token,
)

from datetime import datetime, timezone


router = APIRouter()

def is_refresh_near_expiry(refresh_payload, days=3) -> bool:
    exp = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
    remaining = exp - datetime.now(timezone.utc)
    return remaining.days <= days





@router.post("/refresh-token")
async def refresh_tokens(refresh_token: str =  Header(..., convert_underscores=False)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    # 1️⃣ Verify refresh token
    refresh_payload = verify_refresh_token(refresh_token)
    user_id = refresh_payload["user_id"]

    # 2️⃣ Always issue new auth token
    new_auth = create_auth_token(user_id)

    # 3️⃣ Rotate refresh token ONLY if within 3 days of expiry
    if is_refresh_near_expiry(refresh_payload, days=3):
        new_refresh = create_refresh_token(user_id)
    else:
        new_refresh = refresh_token

    return {
        "status":200,
        "message":"Token generated successfully",
        "auth_token": new_auth,
        "refresh_token": new_refresh
    }
