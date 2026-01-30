from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard

router = APIRouter()

class FeedRequest(BaseModel):
    skip: int = 0
    limit: int = 20

@router.post("/feed")
async def get_feed(payload: FeedRequest, user=Depends(auth_guard)):
    try:
        user_id = user["user_id"]


        skip = payload.skip
        limit = payload.limit

        # --------------------------------------------------
        # 1️⃣ Check if user follows anyone
        # --------------------------------------------------
        following_check = (
            supabase.table("userfollowing")
            .select("following_id")
            .eq("follower_id", user_id)
            .limit(1)
            .execute()
        )
        has_following = bool(following_check.data)

        # --------------------------------------------------
        # 2️⃣ Get posts
        # --------------------------------------------------
        if has_following:
            following_ids = [
                f["following_id"]
                for f in supabase.table("userfollowing")
                .select("following_id")
                .eq("follower_id", user_id)
                .execute()
                .data
            ]

            posts = (
                supabase.table("posts")
                .select("post_id, user_id, post_title, post_content, category, created_at")
                .in_("user_id", following_ids)
                .order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
                .data or []
            )
            # Keep order as-is
            post_ids = [p["post_id"] for p in posts]

        else:
            trending = supabase.rpc(
                "get_trending_post_ids",
                {"p_offset": skip, "p_limit": limit}
            ).execute()
            post_ids = [p["post_id"] for p in trending.data]

            # Fetch full post data preserving RPC order
            posts_data = (
                supabase.table("posts")
                .select("post_id, user_id, post_title, post_content, category, created_at")
                .in_("post_id", post_ids)
                .execute()
                .data or []
            )
            post_map = {p["post_id"]: p for p in posts_data}
            posts = [post_map[pid] for pid in post_ids if pid in post_map]

        if not posts:
            return {
                
                "feed": []
            }

        post_ids = [p["post_id"] for p in posts]
        user_ids = list({p["user_id"] for p in posts})
        category_ids = list({p["category"] for p in posts})

        # --------------------------------------------------
        # 3️⃣ Batch Fetch Related Data
        # --------------------------------------------------
        users = (
            supabase.table("users")
            .select("user_id, user_name, full_name, profile_img_url")
            .in_("user_id", user_ids)
            .execute()
            .data or []
        )
        user_map = {u["user_id"]: u for u in users}

        categories = (
            supabase.table("categories")
            .select("cat_id, cat_title")
            .in_("cat_id", category_ids)
            .execute()
            .data or []
        )
        category_map = {c["cat_id"]: c["cat_title"] for c in categories}

        comments = (
            supabase.table("comments")
            .select("post_id, comment_for")
            .in_("post_id", post_ids)
            .execute()
            .data or []
        )

        likes = (
            supabase.table("likes")
            .select("post_id, user_id")
            .in_("post_id", post_ids)
            .execute()
            .data or []
        )

        images = (
            supabase.table("post_images")
            .select("post_id, image_url, position")
            .in_("post_id", post_ids)
            .order("position")
            .execute()
            .data or []
        )
        image_map = {}
        for img in images:
            image_map.setdefault(img["post_id"], []).append({
                "image_url": img["image_url"],
                "position": img["position"]
            })

        # --------------------------------------------------
        # 4️⃣ Compute Stats
        # --------------------------------------------------
        comment_stats = {}
        for c in comments:
            pid = c["post_id"]
            comment_stats.setdefault(pid, {"support": 0, "deny": 0})
            if c["comment_for"] == "support":
                comment_stats[pid]["support"] += 1
            elif c["comment_for"] == "deny":
                comment_stats[pid]["deny"] += 1

        likes_count = {}
        liked_by_user = set()
        for l in likes:
            likes_count[l["post_id"]] = likes_count.get(l["post_id"], 0) + 1
            if l["user_id"] == user_id:
                liked_by_user.add(l["post_id"])

        # --------------------------------------------------
        # 5️⃣ Build Final Response
        # --------------------------------------------------
        feed = []
        for post in posts:
            pid = post["post_id"]
            stats = comment_stats.get(pid, {"support": 0, "deny": 0})
            total_comments = stats["support"] + stats["deny"]

            support_percent = round((stats["support"] / total_comments) * 100, 2) if total_comments else 0
            deny_percent = round((stats["deny"] / total_comments) * 100, 2) if total_comments else 0

            feed.append({
                "post_id": pid,
                "user": user_map.get(post["user_id"]),
                "post_title": post["post_title"],
                "post_content": post["post_content"],
                "category": {
                    "cat_id": post["category"],
                    "cat_title": category_map.get(post["category"])
                },
                "images": image_map.get(pid, []),
                "likes_count": likes_count.get(pid, 0),
                "comments_count": total_comments,
                "support_percent": support_percent,
                "deny_percent": deny_percent,
                "liked_by_current_user": pid in liked_by_user,
                "created_at": post["created_at"]
            })

        return {
           
            "feed": feed
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FEED_ERROR: {str(e)}")
