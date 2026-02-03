from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard



    
class UserSearchPayload(BaseModel):
    query: str
    limit: int = 20
    last_rank: Optional[float] = None
    last_similarity: Optional[float] = None
    


router = APIRouter()


@router.post("/search/users")
async def search_users(
    payload: UserSearchPayload,
    user=Depends(auth_guard)     # <-- JWT authentication
):
    try:
      
       

        params = {
            "search_query": payload.query,
            "limit_count": payload.limit,
            "last_rank": payload.last_rank,
            "last_similarity": payload.last_similarity
        }

        # 1. Call SQL function
        response = supabase.rpc("search_users", params).execute()
        rows = response.data

        if not rows:
            return {
                "users": [],
                "next_rank": None,
                "next_similarity": None
             
            }

        # ------------------------------------------------------------
        # 2. Merge FTS + TRGM duplicate rows
        # ------------------------------------------------------------
        merged = {}

        for row in rows:
            uid = row["user_id"]

            if uid not in merged:
                merged[uid] = {
                    "user_id": uid,
                    "rank": None,
                    "similarity": None
                }

            if row.get("rank") is not None:
                merged[uid]["rank"] = row["rank"]

            if row.get("similarity") is not None:
                merged[uid]["similarity"] = row["similarity"]

        merged_users = list(merged.values())

        # ------------------------------------------------------------
        # 3. Fetch user details
        # ------------------------------------------------------------
        user_ids = [u["user_id"] for u in merged_users]

        details_response = (
            supabase
            .from_("users")
            .select("user_id, user_name, full_name, profile_img_url")
            .in_("user_id", user_ids)
            .execute()
        )
        details = details_response.data

        details_map = {d["user_id"]: d for d in details}

        # Merge final data
        final_users = []
        for u in merged_users:
            info = details_map.get(u["user_id"], {})
            final_users.append({
                "user_id": u["user_id"],
                "user_name": info.get("user_name"),
                "full_name": info.get("full_name"),
                "profile_img_url": info.get("profile_img_url"),
                "rank": u["rank"],
                "similarity": u["similarity"],
                "score": u["similarity"] or u["rank"]
            })

        # ------------------------------------------------------------
        # 4. Pagination values
        # ------------------------------------------------------------
        next_rank = next((r["rank"] for r in reversed(rows) if r.get("rank") is not None), None)
        next_similarity = next((r["similarity"] for r in reversed(rows) if r.get("similarity") is not None), None)

        # ------------------------------------------------------------
        # 5. RETURN TOKENS + DATA
        # ------------------------------------------------------------
        return {
            "users": final_users,
            "next_rank": next_rank,
            "next_similarity": next_similarity
           
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")



# for post search -----------------------------------------------------

class PostSearchPayload(BaseModel):
    query: str
    limit: int = 20
    last_rank: Optional[float] = None
    last_similarity: Optional[float] = None


@router.post("/search/posts")
async def search_posts(payload: PostSearchPayload, user=Depends(auth_guard)):
    try:
        

        params = {
            "search_query": payload.query,
            "limit_count": payload.limit,
            "last_rank": payload.last_rank,
            "last_similarity": payload.last_similarity
        }

        # 1. Call SQL function
        response = supabase.rpc("search_posts", params).execute()
        rows = response.data

        if not rows:
            return {
                "posts": [],
                "next_rank": None,
                "next_similarity": None
            }

        # 2. Merge duplicate post rows (FTS + TRGM)
        merged = {}
        for row in rows:
            pid = row["post_id"]
            if pid not in merged:
                merged[pid] = {"post_id": pid, "rank": None, "similarity": None}
            if row.get("rank") is not None:
                merged[pid]["rank"] = row["rank"]
            if row.get("similarity") is not None:
                merged[pid]["similarity"] = row["similarity"]

        merged_posts = list(merged.values())

        # 3. Fetch full post details
        post_ids = [p["post_id"] for p in merged_posts]
        posts_query = (
            supabase
            .from_("posts")
            .select("post_id, post_title, post_content")
            .in_("post_id", post_ids)
            .execute()
        )
        posts_details = posts_query.data
        posts_map = {p["post_id"]: p for p in posts_details}

        # 4. Fetch images for posts
        images_query = (
            supabase
            .from_("post_images")
            .select("post_id, image_url, position")
            .in_("post_id", post_ids)
            .order("position", desc=False)  # ascending
            .execute()
        )
        images = images_query.data

        # Map post_id -> list of images
        images_map = {}
        for img in images:
            pid = img["post_id"]
            if pid not in images_map:
                images_map[pid] = []
            images_map[pid].append({
                "url": img["image_url"],
                "position": img["position"]
            })

        # 5. Build final post objects
        final_posts = []
        for post in merged_posts:
            pid = post["post_id"]
            info = posts_map.get(pid, {})
            final_posts.append({
                "post_id": pid,
                "post_title": info.get("post_title"),
                "post_content": info.get("post_content"),
                "images": images_map.get(pid, []),
                "rank": post["rank"],
                "similarity": post["similarity"],
                "score": post["similarity"] or post["rank"]
            })

        # 6. Compute next_rank and next_similarity from merged results
        next_rank = None
        for post in reversed(merged_posts):
            if post.get("rank") is not None:
                next_rank = post["rank"]
                break

        next_similarity = None
        for post in reversed(merged_posts):
            if post.get("similarity") is not None:
                next_similarity = post["similarity"]
                break

        # 7. Return response with tokens
        return {
            "posts": final_posts,
            "next_rank": next_rank,
            "next_similarity": next_similarity
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
