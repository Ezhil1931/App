from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import random

from ..config.supabase_config import supabase
from ..middleware.jwt_auth import auth_guard

router = APIRouter()

# ============================================================
# DATA TRANSFER OBJECTS
# ============================================================

class CategoryCursor(BaseModel):
    b1: Optional[str] = None
    b2: Optional[str] = None
    b3: Optional[str] = None

class CategoryFeedRequest(BaseModel):
    category: str                     # Category title
    cursor: Optional[CategoryCursor] = None
    last_seen: Optional[str] = None   # Client last seen post time
    session_seed: str                 # Seed for shuffle consistency

# ============================================================
# FEED CONFIGURATION
# ============================================================

TOTAL_LIMIT = 20
B1_LIMIT = 8     # 0–2 hours
B2_LIMIT = 7     # 2–12 hours
B3_LIMIT = 5     # 12–48 hours
BUFFER_MINUTES = 45                 # Prevent refresh duplicates
MAX_POSTS_PER_CREATOR = 1          # Soft creator fairness cap

# ============================================================
# UTILITY:  LIGHT  SHUFFLE
# ============================================================

def light_shuffle(items, seed: str):
    r = random.Random(seed)
    r.shuffle(items)
    return items
   
# ============================================================
# CREATOR FAIRNESS MERGE
# ============================================================

def merge_with_creator_soft_cap(buckets, total_limit):
    final_posts = []
    creator_count = {}

    for bucket in buckets:
        for post in bucket:
            uid = post["user_id"]
            creator_count.setdefault(uid, 0)

            if creator_count[uid] >= MAX_POSTS_PER_CREATOR:
                continue

            final_posts.append(post)
            creator_count[uid] += 1

            if len(final_posts) >= total_limit:
                return final_posts

    return final_posts

# ============================================================
# ENRICH POSTS
# - user info
# - likes count
# - comments count
# - support / deny %
# - liked_by_current_user
# ============================================================

def enrich_posts(posts: list, current_user_id: str):
    if not posts:
        return posts

    post_ids = [p["post_id"] for p in posts]
    user_ids = list({p["user_id"] for p in posts})

    # ---------------- USERS ----------------
    users = (
        supabase.table("users")
        .select("user_id, user_name, full_name")
        .in_("user_id", user_ids)
        .execute()
        .data or []
    )
    user_map = {u["user_id"]: u for u in users}

    # ---------------- LIKES ----------------
    likes = (
        supabase.table("likes")
        .select("post_id, user_id")
        .in_("post_id", post_ids)
        .execute()
        .data or []
    )

    likes_count = {}
    liked_by_user = set()
    for l in likes:
        pid = l["post_id"]
        likes_count[pid] = likes_count.get(pid, 0) + 1
        if l["user_id"] == current_user_id:
            liked_by_user.add(pid)

    # ---------------- COMMENTS (SUPPORT / DENY) ----------------
    comments = (
        supabase.table("comments")
        .select("post_id, comment_for")
        .in_("post_id", post_ids)
        .execute()
        .data or []
    )

    comment_stats = {}
    for c in comments:
        pid = c["post_id"]
        comment_stats.setdefault(pid, {"support": 0, "deny": 0})

        if c["comment_for"] == "support":
            comment_stats[pid]["support"] += 1
        elif c["comment_for"] == "deny":
            comment_stats[pid]["deny"] += 1

    # ---------------- MERGE DATA INTO POSTS ----------------
    for post in posts:
        uid = post["user_id"]
        pid = post["post_id"]

        support = comment_stats.get(pid, {}).get("support", 0)
        deny = comment_stats.get(pid, {}).get("deny", 0)
        total_comments = support + deny

        post["user_name"] = user_map.get(uid, {}).get("user_name")
        post["full_name"] = user_map.get(uid, {}).get("full_name")

        post["likes_count"] = likes_count.get(pid, 0)
        post["comments_count"] = total_comments
        post["support_count"] = support
        post["deny_count"] = deny
        post["liked_by_current_user"] = pid in liked_by_user

        if total_comments > 0:
            post["support_percentage"] = round((support / total_comments) * 100, 2)
            post["deny_percentage"] = round((deny / total_comments) * 100, 2)
        else:
            post["support_percentage"] = 0
            post["deny_percentage"] = 0

    return posts

# ============================================================
# CATEGORY FEED ENDPOINT
# ============================================================

@router.post("/category/feed")
async def category_feed(
    payload: CategoryFeedRequest,
    user=Depends(auth_guard)
):
    user_id = user["user_id"]
  

    now = datetime.now(timezone.utc)

    # ---------------- STEP 1: Get category ID ----------------
    cat = (
        supabase.table("categories")
        .select("cat_id")
        .ilike("cat_title", payload.category)
        .limit(1)
        .execute()
        .data
    )

    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    category_id = cat[0]["cat_id"]

    # ---------------- STEP 2: Buffer ----------------
    effective_time = None
    if payload.last_seen:
        effective_time = datetime.fromisoformat(payload.last_seen) - timedelta(minutes=BUFFER_MINUTES)

    cursor = payload.cursor or CategoryCursor()

    # ---------------- STEP 3: Time buckets ----------------
    b1_start = now - timedelta(hours=2)
    b2_start = now - timedelta(hours=12)
    b3_start = now - timedelta(hours=48)

    # ---------------- STEP 4: Bucket fetch ----------------
    def fetch_bucket(start, end, cursor_time, limit):
        q = (
            supabase.table("posts")
            .select("""
                post_id,
                user_id,
                post_title,
                post_content,
                category,
                created_at,
                post_images (
                    image_id,
                    image_url,
                    position
                )
            """)
            .eq("category", category_id)
            .gte("created_at", start.isoformat())
            .lt("created_at", end.isoformat())
            .order("created_at", desc=True)
        )

        if cursor_time:
            q = q.lt("created_at", cursor_time)
        if effective_time:
            q = q.gte("created_at", effective_time.isoformat())

        data = q.limit(limit).execute().data or []

        for post in data:
            post["post_images"] = sorted(post.get("post_images", []), key=lambda x: x["position"])

        return data

    # ---------------- STEP 5: Fetch buckets ----------------
    bucket1 = fetch_bucket(b1_start, now, cursor.b1, B1_LIMIT)
    bucket2 = fetch_bucket(b2_start, b1_start, cursor.b2, B2_LIMIT)
    bucket3 = fetch_bucket(b3_start, b2_start, cursor.b3, B3_LIMIT)

    # ---------------- STEP 6: Shuffle ----------------
    seed = payload.session_seed
    bucket1 = light_shuffle(bucket1, seed + "_b1")
    bucket2 = light_shuffle(bucket2, seed + "_b2")
    bucket3 = light_shuffle(bucket3, seed + "_b3")

    # ---------------- STEP 7: Merge with creator fairness ----------------
    final_posts = merge_with_creator_soft_cap([bucket1, bucket2, bucket3], TOTAL_LIMIT)

    # ---------------- STEP 8: Enrich posts ----------------
    final_posts = enrich_posts(final_posts, current_user_id=user_id)

    # ---------------- STEP 9: Fallback if empty ----------------
    if not final_posts:
        fallback = (
            supabase.table("posts")
            .select("""
                post_id,
                user_id,
                post_title,
                post_content,
                category,
                created_at,
                post_images (
                    image_id,
                    image_url,
                    position
                )
            """)
            .eq("category", category_id)
            .order("created_at", desc=True)
            .limit(TOTAL_LIMIT)
            .execute()
            .data or []
        )
        for post in fallback:
            post["post_images"] = sorted(post.get("post_images", []), key=lambda x: x["position"])
        final_posts = enrich_posts(fallback, current_user_id=user_id)

    # ---------------- STEP 10: Cursor and last_seen ----------------
    next_cursor = {
        "b1": bucket1[-1]["created_at"] if bucket1 else cursor.b1,
        "b2": bucket2[-1]["created_at"] if bucket2 else cursor.b2,
        "b3": bucket3[-1]["created_at"] if bucket3 else cursor.b3
    }
    last_seen_out = max(p["created_at"] for p in final_posts) if final_posts else payload.last_seen

    # ---------------- STEP 11: Return response ----------------
    return {
        "posts": final_posts,
        "next_cursor": next_cursor,
        "last_seen": last_seen_out,
        "has_more": len(final_posts) == TOTAL_LIMIT
        
    }







# category trending  top ten post
from fastapi import Query

@router.get("/trending-ten/category")
async def trending_by_category(
    category_title: str = Query(...),
    limit: int = Query(10),
    user=Depends(auth_guard)
):

    # 1️⃣ Get category ID from title
    category_res = (
        supabase
        .table("categories")
        .select("cat_id")
        .ilike("cat_title", category_title)
        .single()
        .execute()
    )

    if not category_res.data:
        return {"feed": []}

    category_id = category_res.data["cat_id"]

    # 2️⃣ Call RPC using category_id
    rpc = supabase.rpc(
        "get_trending_posts_by_category",
        {
            "p_category": category_id,
            "p_limit": limit
        }
    ).execute()

    post_ids = [row["post_id"] for row in rpc.data]

    if not post_ids:
        return {"feed": []}

    # 3️⃣ Fetch full post data
    posts = (
        supabase.table("posts")
        .select("post_id, user_id, post_title, post_content, category, created_at")
        .in_("post_id", post_ids)
        .execute()
        .data
    )

    return {
        "category": category_title,
        "feed": posts
    }
