from fastapi import Header, HTTPException
from ..utils.jwt_utils import verify_auth_token

async def auth_guard(auth_token: str = Header(...)):
    payload = verify_auth_token(auth_token)

    if not payload:
        raise HTTPException(status_code=401, detail="Auth expired")

    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"user_id": user_id}
