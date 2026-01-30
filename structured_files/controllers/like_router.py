from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import uuid4
from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard
from ..dtos.like_follow import LikeRequest, PostLikePayload

router = APIRouter()

class LikeRequest(BaseModel):
    post_id: str

class PostLikePayload(BaseModel):
    post_id: str




#like the post --------------------------
@router.post("/like", status_code=status.HTTP_201_CREATED)
def like_post(payload: LikeRequest, user=Depends(auth_guard)):
    try:
        user_id = user["user_id"]
       

        existing = (
            supabase.table("likes")
            .select("like_id")
            .eq("user_id", user_id)
            .eq("post_id", payload.post_id)
            .execute()
        )

        if existing.data:
            raise HTTPException(status_code=400, detail="Post already liked")

        like_id = str(uuid4())

        supabase.table("likes").insert({
            "like_id": like_id,
            "post_id": payload.post_id,
            "user_id": user_id,
        }).execute()

        return {
            "status": "success",
            "status_code": status.HTTP_201_CREATED,
            "message": "Post liked successfully",
            "post_id": payload.post_id,
            "like_id": like_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LIKE_ERROR: {str(e)}")
    
#unlike the post-------------------
@router.post("/unlike", status_code=status.HTTP_200_OK)
def unlike_post(payload: LikeRequest, user=Depends(auth_guard)):
    try:        
        user_id = user["user_id"]
      
        res = (
            supabase.table("likes")
            .delete()
            .eq("user_id", user_id)
            .eq("post_id", payload.post_id)
            .execute()
        )

        if not res.data:
            raise HTTPException(status_code=404, detail="Like not found")

        return {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "message": "Post unliked successfully",
            "post_id": payload.post_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"UNLIKE_ERROR: {str(e)}")



#Check if the user like the post or not

@router.post("/is_liked", status_code=status.HTTP_200_OK)
def is_post_liked(payload: PostLikePayload, user=Depends(auth_guard)):
    try:
        user_id = user["user_id"]
        

        res = (
            supabase.table("likes")
            .select("like_id")
            .eq("user_id", user_id)
            .eq("post_id", payload.post_id)
            .execute()
        )

        return {
            "status": "success",
            "status_code": status.HTTP_200_OK,
            "post_id": payload.post_id,
            "liked": True if res.data else False
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IS_LIKED_ERROR: {str(e)}")




#get the user who liked the post


class LikeListPayload(BaseModel):
    post_id: str
    skip: int = 0
    limit: int = 20


@router.post("/likes/users")
async def get_users_who_liked_post(data: LikeListPayload, user=Depends(auth_guard)):

    try:
        

        liked_users = (
            supabase.table("likes")
            .select("user_id")
            .eq("post_id", data.post_id)
            .range(data.skip, data.skip + data.limit - 1)
            .execute()
        )

        return {
            "ok": True,
            "post_id": data.post_id,
            "skip": data.skip,
            "limit": data.limit,
            "users": liked_users.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
