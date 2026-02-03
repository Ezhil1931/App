from pydantic import BaseModel
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException, Depends
from ..middleware.jwt_auth import auth_guard
from ..config.supabase_config import supabase

router = APIRouter()


# -------------------------
# Pydantic Models
# -------------------------

class PostImage(BaseModel):
    image_url: str
    order_number: Optional[int] = 0


class PostItem(BaseModel):
    post_id: str
    caption: Optional[str]
    created_at: str
    images: List[PostImage] = []
    likes_count: Optional[int] = 0
    comments_count: Optional[int] = 0


class UserProfileResponse(BaseModel):
    user: dict
    followers: int
    following: int
    posts: List[PostItem] = []


# -------------------------
# GET /user/{user_id}?limit=20&skip=0
# -------------------------

@router.get("/user/{user_id}", response_model=UserProfileResponse)
async def get_user_data(
    user_id: str,
    limit: int = Query(20, ge=1),
    skip: int = Query(0, ge=0),
    user=Depends(auth_guard)
): 
    current_user_id = user["user_id"]
    
    # -------------------------
    # 1) Get user profile
    # -------------------------
    try:
        user_res = (
            supabase.table("users")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {e}")

    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_res.data

    # -------------------------
    # 2) Get posts with pagination
    # -------------------------
    try:
        posts_res = (
            supabase.table("posts")
            .select("*, post_images(*)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching posts: {e}")

    posts_list = []

    for post in posts_res.data or []:
        # Sort post images by order_number
        images = post.get("post_images") or []
        images.sort(key=lambda x: x.get("order_number", 0))
        post_images = [PostImage(**img) for img in images]

        # Likes count
        like_res = supabase.table("likes").select("*", count="exact").eq("post_id", post["post_id"]).execute()
        likes_count = like_res.count

        # Comments count
        comment_res = supabase.table("comments").select("*", count="exact").eq("post_id", post["post_id"]).execute()
        comments_count = comment_res.count

        posts_list.append(PostItem(
            post_id=post["post_id"],
            caption=post.get("caption"),
            created_at=post.get("created_at"),
            images=post_images,
            likes_count=likes_count,
            comments_count=comments_count
        ))

    # -------------------------
    # 3) Get followers and following counts
    # -------------------------
    followers_res = supabase.table("userfollowing").select("*", count="exact").eq("following_id", user_id).execute()
    following_res = supabase.table("userfollowing").select("*", count="exact").eq("follower_id", user_id).execute()

    followers_count = followers_res.count or 0
    following_count = following_res.count or 0

    # -------------------------
    # 4) Return response
    # -------------------------
    return UserProfileResponse(
        user=user_data,
        followers=followers_count,
        following=following_count,
        posts=posts_list,
        current_user_id=current_user_id
    )
