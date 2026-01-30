# models/user.py
from pydantic import BaseModel, EmailStr,Field
from typing import Optional
from datetime import datetime

class UserUpdatePayload(BaseModel):
    user_name: Optional[str] = Field(None, max_length=255)
    gender: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    profile_img_url: Optional[str] = None
