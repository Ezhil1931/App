from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from datetime import datetime, timezone
import uuid

from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard

STORAGE_BUCKET = "users"
router = APIRouter()


def upload_profile_image(user_id: str, file: UploadFile):
    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"profile_{uuid.uuid4()}.{ext}"
    storage_path = f"{user_id}/profile_img/{filename}"

    file.file.seek(0)
    file_bytes = file.file.read()

    response = supabase.storage.from_(STORAGE_BUCKET).upload(
        path=storage_path,
        file=file_bytes
    )

    if hasattr(response, "error") and response.error:
        raise Exception(response.error)

    public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(storage_path)
    return public_url, storage_path


def delete_file(path: str):
    try:
        result = supabase.storage.from_(STORAGE_BUCKET).remove([path])
        return isinstance(result, list) and len(result) > 0
    except Exception:
        return False


@router.put("/profile/update")
async def update_profile(
    user_name:Optional[str]=Form(None),
    full_name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    profile_pic: Optional[UploadFile] = File(None),
    user=Depends(auth_guard)
):
    # ✅ Auth user
    user_id = user["user_id"]
   

    # Fetch existing user
    
    result = supabase.table("users").select(
        "user_name, full_name, bio, profile_img_url"
    ).eq("user_id", user_id).limit(1).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    existing = result.data[0]
    update_data = {}
    
        # ✅ Check if username already exists (excluding current user)
    if user_name:
        existing_username = (
            supabase.table("users")
            .select("user_id")
            .ilike("user_name", user_name)
            .execute()
        )

        if existing_username.data:
            raise HTTPException(
                status_code=409,
                detail="Username already exists"
            )



    if user_name:
        update_data["user_name"] = user_name
    

    if full_name:
        update_data["full_name"] = full_name

    if bio:
        update_data["bio"] = bio

    if profile_pic:
        new_url, new_path = upload_profile_image(user_id, profile_pic)

        old_url = existing.get("profile_img_url")
        if old_url and STORAGE_BUCKET in old_url:
            old_path = old_url.split(f"/{STORAGE_BUCKET}/")[-1]
            delete_file(old_path)

        update_data["profile_img_url"] = new_url


    update_data["modified_at"] = datetime.now(timezone.utc).isoformat()
    update_data["modified_by"] = user_id    
    supabase.table("users").update(update_data).eq("user_id", user_id).execute()

    return {
        "status": 200,
        "message": "Profile updated successfully"
       
    }
