from fastapi import Header, HTTPException
from ..utils.jwt_utils import verify_auth_token

async def auth_guard(auth_token: str = Header(None)):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Missing auth token")

    payload = verify_auth_token(auth_token)
    user_id=payload["user_id"]

    if not payload:
        raise HTTPException(status_code=401, detail="Auth expired")
    

    return {
        "user_id":user_id
         }
