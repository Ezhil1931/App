import jwt
from datetime import datetime, timedelta,timezone
from fastapi import HTTPException
from .rsa_keys import PRIVATE_KEY, PUBLIC_KEY



ALGORITHM = "RS256"

#create the token ----------------------------

def create_auth_token(user_id: str):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(weeks=1)
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=ALGORITHM)

#verify the token -------------------------------



def verify_auth_token(token: str):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # auth expired → frontend must use refresh token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid auth token")


def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


#it is for verifiaction token ------------------
def create_verification_token(user_id: str) -> str:

    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    return token

def verify_verification_token(token: str) -> str:
   
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        raise Exception("Verification token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid verification token")