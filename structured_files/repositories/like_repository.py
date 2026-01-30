from datetime import datetime
from ..config.supabase_config import supabase

class LikeRepository:

    @staticmethod
    async def add_like(post_id: str, user_id: str):
        created_at = datetime.utcnow().isoformat()

        data = {
            "post_id": post_id,
            "user_id": user_id,
            "created_at": created_at
        }

        response = supabase.table("likes").insert(data).execute()
        return response.data

    @staticmethod
    async def remove_like(post_id: str, user_id: str):
        response = supabase.table("likes") \
            .delete() \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()
        return response.data

    @staticmethod
    async def check_if_liked(post_id: str, user_id: str):
        response = supabase.table("likes") \
            .select("*") \
            .eq("post_id", post_id) \
            .eq("user_id", user_id) \
            .execute()

        return len(response.data) > 0

    @staticmethod
    async def get_likes_count(post_id: str):
        response = supabase.table("likes") \
            .select("like_id") \
            .eq("post_id", post_id) \
            .execute()

        return len(response.data)

    @staticmethod
    async def get_users_who_liked(post_id: str):
        response = (
            supabase
            .table("likes")
            .select("user_id")
            .eq("post_id", post_id)
            .execute()
        )
        return [row["user_id"] for row in response.data]
