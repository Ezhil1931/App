
from pydantic import BaseModel, EmailStr




class LoginRequest(BaseModel):
    user_email: EmailStr
    password: str


class SignUpRequest(BaseModel):
    user_email: EmailStr
    password: str

