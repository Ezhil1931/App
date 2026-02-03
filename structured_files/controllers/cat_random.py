from pydantic import BaseModel
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from ..middleware.jwt_auth import auth_guard
from ..config.supabase_config import supabase

#this is for dahan ssaid exclude some post and send remaining post for category feed


class CategoryRandomFeedRequest(BaseModel):
    category_title: str
    exclude_post_ids: List[str] = []
    limit: int = 20


router = APIRouter()


@router.post("/category/random-feed")
async def get_random_posts_by_category(
    payload: CategoryRandomFeedRequest,
    user=Depends(auth_guard)
):
    try:
        # 1️⃣ Get category id from title
        cat_res = (
            supabase
            .table("categories")
            .select("cat_id")
            .ilike("cat_title", payload.category_title)
            .execute()
        )

        if not cat_res.data or len(cat_res.data) == 0:
            raise HTTPException(status_code=404, detail="Category not found")

        # ✅ FIX: access first row
        cat_id = cat_res.data[0]["cat_id"]

        # 2️⃣ Fetch posts with like & comment counts
        query = (
            supabase
            .table("posts")
            .select("""
                post_id,
                post_title,
                post_content,
                created_at,

                likes_count:likes(count),
                comments_count:comments(count),

                users:user_id (
                    user_id,
                    user_name,
                    full_name,
                    profile_img_url
                ),
                post_images (
                    image_id,
                    image_url,
                    position
                )
            """)
            .eq("category", cat_id)
        )

        # 3️⃣ Exclude already fetched posts
        if payload.exclude_post_ids:
            query = query.not_.in_("post_id", payload.exclude_post_ids)

        # 4️⃣ Order + limit
        query = query.order("created_at", desc=True).limit(payload.limit)

        res = query.execute()

        # 5️⃣ Normalize counts (IMPORTANT)
        posts = []
        for post in res.data:
            post["likes_count"] = (
                post["likes_count"][0]["count"]
                if post.get("likes_count") and len(post["likes_count"]) > 0
                else 0
            )
            post["comments_count"] = (
                post["comments_count"][0]["count"]
                if post.get("comments_count") and len(post["comments_count"]) > 0
                else 0
            )
            posts.append(post)

        return {
            "category": payload.category_title,
            "posts": posts,
            "count": len(posts)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
