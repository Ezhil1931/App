from fastapi import FastAPI, HTTPException,APIRouter
from pydantic import BaseModel, constr
from typing import Annotated
from ..config.supabase_config import supabase

router=APIRouter()

class UsernameCheckPayload(BaseModel):
    user_name: Annotated[str, constr(min_length=3, max_length=30)]



@router.post("/username")
async def check_username(payload: UsernameCheckPayload):

    user_name = payload.user_name

    try:
        # Query Supabase for existing username
        response = supabase.table("users").select("user_id").eq("user_name", user_name).execute()

        if response.data:  # Username exists
            return {"available": False, "message": "Username already taken"}
        else:  # Username available
            return {"available": True, "message": "Username is available"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
