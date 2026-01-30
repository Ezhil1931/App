from pydantic import BaseModel, Field
from typing import Optional



class UserCreate(BaseModel):
    
    user_name: str = Field(..., max_length=255)
    gender: Optional[str] = Field(None, max_length=50)
    phone_number: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    profile_img_url: Optional[str] = None
 
    

