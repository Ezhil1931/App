import uuid
from datetime import datetime
from ..config.supabase_config import supabase


class FollowingRepository:

    # 1️⃣ Follow a user
    @staticmethod
    async def follow_user(follower_id: str, following_id: str):

        # Prevent self follow
        if follower_id == following_id:
            raise ValueError("User cannot follow themselves")

        # Check if already following
        existing = supabase.table("userfollowing")\
            .select("follow_id")\
            .eq("follower_id", follower_id)\
            .eq("following_id", following_id)\
            .execute()

        if existing.data:
            return {"already_following": True}

        data = {
            "follow_id": str(uuid.uuid4()),
            "follower_id": follower_id,
            "following_id": following_id,
            "created_at": datetime.utcnow().isoformat()
        }

        return supabase.table("userfollowing").insert(data).execute()

    # 2️⃣ Unfollow user
    @staticmethod
    async def unfollow_user(follower_id: str, following_id: str):
        return supabase.table("userfollowing")\
            .delete()\
            .eq("follower_id", follower_id)\
            .eq("following_id", following_id)\
            .execute()

    # 3️⃣ Check if user A follows user B
    @staticmethod
    async def is_following(follower_id: str, following_id: str):
        res = supabase.table("userfollowing")\
            .select("follow_id")\
            .eq("follower_id", follower_id)\
            .eq("following_id", following_id)\
            .execute()

        return len(res.data) > 0

    # 4️⃣ Get list of users that FOLLOW a specific user
    @staticmethod
    async def get_followers(user_id: str, skip=0, limit=20):
        return supabase.table("userfollowing")\
            .select("""
                follower_id,
                users:follower_id(user_name, full_name, profile_img_url)
            """)\
            .eq("following_id", user_id)\
            .range(skip, skip + limit - 1)\
            .execute()

    # 5️⃣ Get list of users that user is following
    @staticmethod
    async def get_following(user_id: str, skip=0, limit=20):
        return supabase.table("userfollowing")\
            .select("""
                following_id,
                users:following_id(user_name, full_name, profile_img_url)
            """)\
            .eq("follower_id", user_id)\
            .range(skip, skip + limit - 1)\
            .execute()

    # 6️⃣ Count followers for user
    @staticmethod
    async def count_followers(user_id: str):
        res = supabase.table("userfollowing")\
            .select("follow_id", count="exact")\
            .eq("following_id", user_id)\
            .execute()
        return res.count if res else 0

    # 7️⃣ Count following for user
    @staticmethod
    async def count_following(user_id: str):
        res = supabase.table("userfollowing")\
            .select("follow_id", count="exact")\
            .eq("follower_id", user_id)\
            .execute()
        return res.count if res else 0

    # 8️⃣ Get mutual follow (friends)
    @staticmethod
    async def get_mutual_follow(user1: str, user2: str):
        user1_follows_user2 = await FollowingRepository.is_following(user1, user2)
        user2_follows_user1 = await FollowingRepository.is_following(user2, user1)
        return user1_follows_user2 and user2_follows_user1

    # 9️⃣ Suggest users to follow (not already followed)
    @staticmethod
    async def suggested_users(user_id: str, limit=20):

        # Get all followed users
        followed = supabase.table("userfollowing")\
            .select("following_id")\
            .eq("follower_id", user_id)\
            .execute()

        followed_ids = [row["following_id"] for row in followed.data]

        if not followed_ids:
            followed_ids = ["NOUSER"]  

        # Get users NOT followed + not self
        return supabase.table("users")\
            .select("user_id, user_name, full_name, profile_img_url")\
            .not_.in_("user_id", followed_ids + [user_id])\
            .limit(limit)\
            .execute()

    # 🔟 Get following list raw IDs only
    @staticmethod
    async def get_following_ids(user_id: str):
        res = supabase.table("userfollowing")\
            .select("following_id")\
            .eq("follower_id", user_id)\
            .execute()

        return [row["following_id"] for row in res.data]

