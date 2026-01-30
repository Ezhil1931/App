import uuid
from datetime import datetime, timezone
from argon2 import PasswordHasher
from typing import Optional
from ..config.supabase_config import supabase

ph = PasswordHasher()

STORAGE_BUCKET = "users"

class UserRepository:
  
  #check email already exists
    @staticmethod
    def get_user_by_email(email: str):
        return (
            supabase.table("users")
            .select("user_id")
            .eq("user_email", email)
            .execute()
            .data
        )
    
    # insert new user data
    @staticmethod
    def create_user(data: dict):
        return supabase.table("users").insert(data).execute()
    
    #get user data using email and pass
    @staticmethod
    def get_user_by_credential(email: str):
        resp = (
            supabase.table("users")
            .select("user_id,user_email,password,verified,last_sign_in")
            .eq("user_email", email)
            .execute()
        )
        return resp.data if resp.data else None
    
    #Update last sign in 
    @staticmethod
    def update_last_sign_in(user_id: str):
        resp = (
            supabase.table("users")
            .update({
                "last_sign_in": datetime.now(timezone.utc).isoformat()
            })
            .eq("user_id", user_id)
            .execute()
        )

        if not resp.data:
            raise Exception("Last sign-in update failed")

        return True
    

   

