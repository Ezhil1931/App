


from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from uuid import uuid4

from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard

router = APIRouter()



class FollowPayload(BaseModel):
    following_id: str


# ----------------- Follow a user -----------------
@router.post("/follow", status_code=status.HTTP_200_OK)
def follow_user(payload: FollowPayload, user=Depends(auth_guard)):

    follower_id= user["user_id"]
    



    following_id = payload.following_id
    

    if follower_id == following_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    try:
        existing = (
            supabase.table("userfollowing")
            .select("*")
            .eq("follower_id", follower_id)
            .eq("following_id", following_id)
            .execute()
        )

        if existing.data:
            return {
                "status": "success",
                "message": "Already following"
            }

        follow_id = str(uuid4())
        result = (
            supabase.table("userfollowing")
            .insert({
                "follow_id": follow_id,
                "follower_id": follower_id,
                "following_id": following_id
            })
            .execute()
        )

        return {
            "status": "success",
            "message": "Followed successfully",
            "follow_id": follow_id
           
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- Unfollow a user -----------------
@router.post("/unfollow", status_code=status.HTTP_200_OK)
def unfollow_user(payload: FollowPayload,user=Depends(auth_guard)):

    follower_id=user["user_id"]
    following_id = payload.following_id
   
    
   
    try:
        result = (
            supabase.table("userfollowing")
            .delete()
            .eq("follower_id", follower_id)
            .eq("following_id", following_id)
            .execute()
        )

        return {
            "status": "success",
            "message": "Unfollowed successfully"
            
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------- Get followers data -----------------


class PagingPayload(BaseModel):
    skip: int = 0
    limit: int = 20
    

@router.post("/followers", status_code=status.HTTP_200_OK)
def get_followers(payload: PagingPayload, user=Depends(auth_guard)):

    user_id = user["user_id"]
  

    # Step 1) Get only follower_id
    res = (
        supabase.table("userfollowing")
        .select("follower_id")
        .eq("following_id", user_id)
        .range(payload.skip, payload.skip + payload.limit - 1)
        .execute()
    )

    follower_ids = [x["follower_id"] for x in res.data] if res.data else []

    if not follower_ids:
        return {
            "status": "success",
            "followers": [],
            "skip": payload.skip,
            "limit": payload.limit
          
        }

    # Step 2) Fetch full user data
    user_res = (
        supabase.table("users")
        .select("user_id, user_name, full_name,profile_img_url")
        .in_("user_id", follower_ids)
        .execute()
    )

    return {
        "status": "success",
        "followers": user_res.data,
        "skip": payload.skip,
        "limit": payload.limit
       
    }


#get following ----------------]


@router.post("/following", status_code=status.HTTP_200_OK)
def get_following(payload: PagingPayload, user=Depends(auth_guard)):
    
    user_id = user["user_id"]
    

    # Step 1) Get only following_id
    res = (
        supabase.table("userfollowing")
        .select("following_id")
        .eq("follower_id", user_id)
        .range(payload.skip, payload.skip + payload.limit - 1)
        .execute()
    )

    following_ids = [x["following_id"] for x in res.data] if res.data else []

    if not following_ids:
        return {
            "status": "success",
            "following": [],
            "skip": payload.skip,
            "limit": payload.limit
        }

    # Step 2) Fetch profile info
    user_res = (
        supabase.table("users")
        .select("user_id, user_name, full_name, profile_img_url")
        .in_("user_id", following_ids)
        .execute()
    )

    return {
        "status": "success",
        "following": user_res.data,
        "skip": payload.skip,
        "limit": payload.limit
    }
