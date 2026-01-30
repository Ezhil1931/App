from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from typing import List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel
from ..middleware.jwt_auth import auth_guard
from ..config.supabase_config import supabase

router = APIRouter()
STORAGE_BUCKET = "users"


# ============================
# CREATE POST
# ============================
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_post(
    post_title: str = Form(...),
    content: str = Form(...),
    cat_title: str = Form(...),   # 👈 category title
    files: Optional[List[UploadFile]] = File(None),
    user=Depends(auth_guard)
):
    try:
        user_id = user["user_id"]
   

        post_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # 1️⃣ Category lookup
        cat_res = (
            supabase.table("categories")
            .select("cat_id, cat_title")
            .ilike("cat_title", cat_title)
            .execute()
        )

        if not cat_res.data:
            return {
                "status": "failed",
                "message": f"Category '{cat_title}' not found"
            }

        cat_id = cat_res.data[0]["cat_id"]

        # 2️⃣ Insert post record
        supabase.table("posts").insert({
            "post_id": post_id,
            "post_title": post_title,
            "post_content": content,
            "category": cat_id,           
            "user_id": user_id,
            "created_at": timestamp,
            "modified_at": timestamp,
            "created_by": user_id,
            "modified_by": user_id
        }).execute()

        # 3️⃣ Image uploads
        image_urls = []
        position_index = 0

        if files:
            for img in files:
                ext = img.filename.split(".")[-1]
                image_id = str(uuid.uuid4())
                filename = f"{post_id}_{image_id}.{ext}"
                file_path = f"{user_id}/post_img/{filename}"

                file_bytes = await img.read()

                supabase.storage.from_(STORAGE_BUCKET).upload(
                    file_path,
                    file_bytes,
                    {"content-type": img.content_type}
                )

                public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_path)
                image_urls.append(public_url)

                supabase.table("post_images").insert({
                    "image_id": image_id,
                    "post_id": post_id,
                    "image_url": public_url,
                    "position": position_index
                }).execute()

                position_index += 1

        return {
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": "Post created successfully",
            "post_id": post_id,
            "category": {
                "cat_id": cat_id,
                "cat_title": cat_title
            },
            "image_urls": image_urls
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POST_CREATE_ERROR: {str(e)}")


# ============================
# UPDATE POST
# ============================


class UpdatePostPayload(BaseModel):
    post_id: str
    post_title: str
    content: str

@router.put("/update", status_code=status.HTTP_200_OK)
async def update_post(
    payload: UpdatePostPayload,
    user=Depends(auth_guard)
):
    try:
        user_id = user["user_id"]
        new_auth = user["new_auth"]
        new_refresh = user["new_refresh"]
        post_id = payload.post_id

        post = supabase.table("posts") \
            .select("post_id") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found or unauthorized")

        supabase.table("posts").update({
            "post_title": payload.post_title,
            "post_content": payload.content,
            "modified_at": datetime.utcnow().isoformat(),
            "modified_by": user_id
        }).eq("post_id", post_id).execute()

        return {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Post updated successfully",
            "post_id": post_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POST_UPDATE_ERROR: {str(e)}")


# ============================
# DELETE POST
# ============================

class DeletePostPayload(BaseModel):
    post_id: str


@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_post(payload: DeletePostPayload, user=Depends(auth_guard)):
    try:
        post_id = payload.post_id
        user_id = user["user_id"]

        post = supabase.table("posts") \
            .select("*") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found or unauthorized")

        img_rows = supabase.table("post_images").select("*").eq("post_id", post_id).execute()

        delete_filepaths = []

        for img in img_rows.data:
            image_url = img["image_url"]
            cleaned = image_url.split('?')[0]
            path_after_bucket = cleaned.split(f"{STORAGE_BUCKET}/")[-1]
            file_path = path_after_bucket

            delete_filepaths.append(file_path)

        if delete_filepaths:
            supabase.storage.from_(STORAGE_BUCKET).remove(delete_filepaths)

        supabase.table("post_images").delete().eq("post_id", post_id).execute()
        supabase.table("comments").delete().eq("post_id", post_id).execute()
        supabase.table("likes").delete().eq("post_id", post_id).execute()
        supabase.table("posts").delete().eq("post_id", post_id).execute()

        return {
            "status": "success",
            "message": "Post deleted successfully",
            "post_id": post_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POST_DELETE_ERROR: {str(e)}")



#----------------get the single post data 


class GetPostRequest(BaseModel):
    post_id: str
@router.post("/get", status_code=status.HTTP_200_OK)
async def get_single_post(payload: GetPostRequest, user=Depends(auth_guard)):

    try:
        user_id = user["user_id"]

        post_id = payload.post_id

        # 1️⃣ Fetch post 
        post = supabase.table("posts") \
            .select("*") \
            .eq("post_id", post_id) \
            .execute()

        if not post.data:
            raise HTTPException(status_code=404, detail="Post not found")

        post_data = post.data[0]
        post_owner_id = post_data["user_id"]

        # ⭐ 1.1 Fetch user info of the post owner
        user_row = supabase.table("users") \
            .select("user_name, full_name, profile_img_url") \
            .eq("user_id", post_owner_id) \
            .execute()

        user_info = user_row.data[0] if user_row.data else {
            "user_name": None,
            "full_name": None,
            "profile_img_url": None
        }

        # 2️⃣ resolve category title
        category = None
        if "category" in post_data and post_data["category"]:
            cat_row = supabase.table("categories") \
                .select("cat_title") \
                .eq("cat_id", post_data["category"]) \
                .execute()

            if cat_row.data:
                category = cat_row.data[0]["cat_title"]

        # 3️⃣ Fetch post_images with position
        img_rows = supabase.table("post_images") \
            .select("image_url, position") \
            .eq("post_id", post_id) \
            .order("position", desc=False) \
            .execute()

        images = []
        if img_rows.data:
            for img in img_rows.data:
                images.append({
                    "image_url": img["image_url"],
                    "position": img["position"]
                })

        # 4️⃣ Count likes
        likes = supabase.table("likes") \
            .select("like_id") \
            .eq("post_id", post_id) \
            .execute()

        likes_count = len(likes.data)

        # 5️⃣ Count comments + support/deny percentages
        comments = supabase.table("comments") \
            .select("comment_id, comment_for") \
            .eq("post_id", post_id) \
            .execute()

        total_comments = len(comments.data)

        support_count = 0
        deny_count = 0
        
        for c in comments.data:
            if c["comment_for"] == "support":
                support_count += 1
            elif c["comment_for"] == "deny":
                deny_count += 1

        # Percentages
        if total_comments > 0:
            support_percentage = round((support_count / total_comments) * 100, 2)
            deny_percentage = round((deny_count / total_comments) * 100, 2)
        else:
            support_percentage = 0
            deny_percentage = 0

        # 6️⃣ Check if user liked
        user_like = supabase.table("likes") \
            .select("like_id") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        is_liked_by_user = True if user_like.data else False

        return {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Post fetched successfully",
            "user":{
           
                "user_name": user_info["user_name"],
                "full_name": user_info["full_name"],
                "profile_img_url": user_info["profile_img_url"]

            },
            "post": {
                "post_id": post_data["post_id"],
                "user_id": post_owner_id,
                "post_title": post_data["post_title"],
                "post_content": post_data["post_content"],
                "category_id": post_data["category"],
                "category": category,
                "created_at": post_data["created_at"],
                "modified_at": post_data["modified_at"],

               
            },
            "images": images,
            "counts": {
                "likes": likes_count,
                "comments": total_comments,
                "support_count": support_count,
                "deny_count": deny_count,
                "support_percentage": support_percentage,
                "deny_percentage": deny_percentage
            },
            "user_actions": {
                "liked_by_user": is_liked_by_user
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POST_GET_ERROR: {str(e)}")
