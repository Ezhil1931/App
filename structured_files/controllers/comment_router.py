from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime

from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard


router = APIRouter()


# ============================
# Pydantic Payloads
# ============================

class CommentPayload(BaseModel):
    post_id: str
    parent_comment_id: Optional[str] = None
    comment_text: str
    comment_for: str

class UpdateCommentPayload(BaseModel):
    comment_id: str
    new_comment_text: str

class DeleteCommentRequest(BaseModel):
    comment_id: str

class PostCommentsRequest(BaseModel):
    post_id: str

class CommentRepliesRequest(BaseModel):
    comment_id: str


# ============================
# CREATE COMMENT
# ============================
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_comment(payload: CommentPayload, user=Depends(auth_guard)):

    user_id = user["user_id"]
  

    comment_id = str(uuid4())
    timestamp = datetime.utcnow().isoformat()

    parent_id = payload.parent_comment_id or None

    supabase.table("comments").insert({
        "comment_id": comment_id,
        "post_id": payload.post_id,
        "user_id": user_id,
        "parent_comment_id": parent_id,
        "comment_text": payload.comment_text,
        "comment_for": payload.comment_for,     # enum: 'deny' | 'support'
        
        # required values
        "created_by": user_id,
        "created_at": timestamp,

        # null on first insert
        "modified_by":user_id,
        "modified_at": timestamp
    }).execute()

    return {
        "status": "success",
        "status_code": status.HTTP_201_CREATED,
        "message": "Comment added successfully",
        "comment_id": comment_id,
        "created_by": user_id,
        "created_at": timestamp,
        "parent_comment_id": parent_id
       
    }


# ============================
# UPDATE COMMENT
# ============================

@router.put("/update", status_code=status.HTTP_200_OK)
async def update_comment(payload: UpdateCommentPayload, user=Depends(auth_guard)):

    user_id = user["user_id"]


    existing = (
        supabase.table("comments")
        .select("user_id")
        .eq("comment_id", payload.comment_id)
        .single()
        .execute()
    ).data

    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")

    if existing["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You cannot edit this comment")

    timestamp = datetime.utcnow().isoformat()

    supabase.table("comments").update({
        "comment_text": payload.new_comment_text,
        "modified_by": user_id,
        "modified_at": timestamp
    }).eq("comment_id", payload.comment_id).execute()

    return {
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Comment updated successfully",
        "comment_id": payload.comment_id,
        "modified_by": user_id,
        "modified_at": timestamp
     
    }


# ============================
# DELETE COMMENT
# ============================
@router.delete("/delete", status_code=status.HTTP_200_OK)
async def delete_comment(payload: DeleteCommentRequest, user=Depends(auth_guard)):

    user_id = user["user_id"]
  

    existing = (
        supabase.table("comments")
        .select("user_id")
        .eq("comment_id", payload.comment_id)
        .single()
        .execute()
    ).data

    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")

    if existing["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You cannot delete this comment")

    # delete this comment
    supabase.table("comments").delete().eq("comment_id", payload.comment_id).execute()
    
    # delete replies of this comment
    supabase.table("comments").delete().eq("parent_comment_id", payload.comment_id).execute()

    return {
        "status": "success",
        "status_code": status.HTTP_200_OK,
        "message": "Comment deleted successfully",
        "comment_id": payload.comment_id
     
    }



# ============================
# GET COMMENTS (nested replies)
# ============================

class PostCommentsPagedRequest(BaseModel):
    post_id: str
    skip: int = 0
    limit: int = 10


class CommentRepliesPagedRequest(BaseModel):
    comment_id: str
    skip: int = 0
    limit: int = 2

@router.post("/comment_list", status_code=status.HTTP_200_OK)
async def get_comments(payload: PostCommentsPagedRequest, user=Depends(auth_guard)):
    
    user_id = user["user_id"]

    res = (
        supabase.table("comments")
        .select("*")
        .eq("post_id", payload.post_id)
        .is_("parent_comment_id", None)
        .order("created_at", desc=False)
        .range(payload.skip, payload.skip + payload.limit - 1)
        .execute()
    )

    original = res.data or []

    final_comments = []

    for c in original:
        
        comment_owner_id = c["user_id"]

        user_info = (
            supabase.table("users")
            .select("user_name, profile_img_url")
            .eq("user_id", comment_owner_id)
            .single()
            .execute()
        )

        final_comment = {
            "comment_id": c["comment_id"],
            "user_name": user_info.data.get("user_name"),
            "profile_img_url": user_info.data.get("profile_img_url"),
            "text": c.get("comment_text"),
            "created_at": c.get("created_at"),   # <- raw timestamp
            "owned_by_me": (comment_owner_id == user_id),
        }

        replies_res = (
            supabase.table("comments")
            .select("*")
            .eq("parent_comment_id", c["comment_id"])
            .order("created_at", desc=False)
            .limit(2)
            .execute()
        )

        replies = replies_res.data or []
        final_replies = []

        for r in replies:
            reply_user_info = (
                supabase.table("users")
                .select("user_name, profile_img_url")
                .eq("user_id", r["user_id"])
                .single()
                .execute()
            )

            final_replies.append({
                "comment_id": r["comment_id"],
                "user_name": reply_user_info.data.get("user_name"),
                "profile_img_url": reply_user_info.data.get("profile_img_url"),
                "text": r.get("comment_text"),
                "created_at": r.get("created_at"),  # <- raw timestamp
                "owned_by_me": (r["user_id"] == user_id),
            })

        final_comment["replies"] = final_replies

        count_res = (
            supabase.table("comments")
            .select("comment_id", count="exact")
            .eq("parent_comment_id", c["comment_id"])
            .execute()
        )

        final_comment["reply_count"] = count_res.count
        final_comment["show_more_replies"] = count_res.count > 2

        final_comments.append(final_comment)

    return {
        "status": "success",
        "comments": final_comments
       
    }

#load the replies -----------------------------------
@router.post("/more_replies", status_code=status.HTTP_200_OK)
async def get_more_replies(payload: CommentRepliesPagedRequest, user=Depends(auth_guard)):
    
    user_id = user["user_id"]


    res = (
        supabase.table("comments")
        .select("*")
        .eq("parent_comment_id", payload.comment_id)
        .order("created_at", desc=False)
        .range(payload.skip, payload.skip + payload.limit - 1)
        .execute()
    )

    replies = res.data or []

    final_replies = []

    for r in replies:

        user_info = (
            supabase.table("users")
            .select("user_name, profile_img_url")
            .eq("user_id", r["user_id"])
            .single()
            .execute()
        )

        final_replies.append({
            "comment_id": r["comment_id"],
            "user_name": user_info.data.get("user_name"),
            "profile_img_url": user_info.data.get("profile_img_url"),
            "text": r.get("comment_text"),
            "created_at": r.get("created_at"),    # raw ISO timestamp
            "owned_by_me": (r.get("user_id") == user_id),
        })

    return {
        "status": "success",
        "comment_id": payload.comment_id,
        "skip": payload.skip,
        "limit": payload.limit,
        "replies": final_replies
        
    }
