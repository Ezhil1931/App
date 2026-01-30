import uuid
from datetime import datetime
from ..config.supabase_config import supabase


class CommentsRepository:

    # 1️⃣ Add comment or reply
    @staticmethod
    async def create_comment(
        post_id: str,
        user_id: str,
        comment_text: str,
        comment_for: str = "support",  # ENUM: support / deny
        parent_comment_id: str = None
    ):

        if comment_for not in ["support", "deny"]:
            raise ValueError("Invalid comment_for enum value")

        data = {
            "comment_id": str(uuid.uuid4()),
            "post_id": post_id,
            "user_id": user_id,
            "comment_text": comment_text,
            "comment_for": comment_for,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id,
            "parent_comment_id": parent_comment_id,
            "modified_at": None,
            "modified_by": None
        }

        return supabase.table("comments").insert(data).execute()

    # 2️⃣ Update a comment (only by owner)
    @staticmethod
    async def update_comment(comment_id: str, user_id: str, new_text: str, new_comment_for: str):

        if new_comment_for not in ["support", "deny"]:
            raise ValueError("Invalid comment_for enum value")

        return supabase.table("comments")\
            .update({
                "comment_text": new_text,
                "comment_for": new_comment_for,
                "modified_at": datetime.utcnow().isoformat(),
                "modified_by": user_id
            })\
            .eq("comment_id", comment_id)\
            .eq("user_id", user_id)\
            .execute()

    # 3️⃣ Delete comment (only owner)
    @staticmethod
    async def delete_comment(comment_id: str, user_id: str):
        return supabase.table("comments")\
            .delete()\
            .eq("comment_id", comment_id)\
            .eq("user_id", user_id)\
            .execute()

    # 4️⃣ Get top-level comments for post (paginated)
    @staticmethod
    async def get_comments_for_post(post_id: str, skip=0, limit=20):
        return supabase.table("comments")\
            .select("*")\
            .eq("post_id", post_id)\
            .is_("parent_comment_id", None)\
            .order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()

    # 5️⃣ Get replies for a specific comment
    @staticmethod
    async def get_replies(comment_id: str, skip=0, limit=50):
        return supabase.table("comments")\
            .select("*")\
            .eq("parent_comment_id", comment_id)\
            .order("created_at", asc=True)\
            .range(skip, skip + limit - 1)\
            .execute()

    # 6️⃣ Count total comments for a post
    @staticmethod
    async def count_comments(post_id: str):
        res = supabase.table("comments")\
            .select("comment_id", count="exact")\
            .eq("post_id", post_id)\
            .execute()
        return res.count if res else 0

    # 7️⃣ Count replies for a comment
    @staticmethod
    async def count_replies(comment_id: str):
        res = supabase.table("comments")\
            .select("comment_id", count="exact")\
            .eq("parent_comment_id", comment_id)\
            .execute()
        return res.count if res else 0

    # 8️⃣ Check if user owns comment
    @staticmethod
    async def user_owns_comment(comment_id: str, user_id: str):
        res = supabase.table("comments")\
            .select("comment_id")\
            .eq("comment_id", comment_id)\
            .eq("user_id", user_id)\
            .execute()

        return len(res.data) > 0

    # 9️⃣ Get full comment with owner profile info
    @staticmethod
    async def get_comments_with_user(post_id: str, skip=0, limit=20):

        return supabase.table("comments")\
            .select("""
                comment_id,
                post_id,
                user_id,
                comment_text,
                comment_for,
                created_at,
                modified_at,
                modified_by,
                parent_comment_id,
                users:user_id(user_name, full_name, profile_img_url)
            """)\
            .eq("post_id", post_id)\
            .is_("parent_comment_id", None)\
            .order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()

    # 🔟 Get a single comment by ID
    @staticmethod
    async def get_comment_by_id(comment_id: str):
        return supabase.table("comments")\
            .select("*")\
            .eq("comment_id", comment_id)\
            .single()\
            .execute()
