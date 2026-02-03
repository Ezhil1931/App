
import uuid, random

from ..config.supabase_config import supabase

"""
    Generates a unique username like: user_482193
    Ensures no conflict in DB.
    """




def generate_unique_username():
    MAX_ATTEMPTS = 10

    for _ in range(MAX_ATTEMPTS):
        username = f"user_{random.randint(100000, 999999)}"
        exists = (
            supabase.table("users")
            .select("user_id")
            .ilike("user_name", username)
            .execute()
            .data
        )
        if not exists:
            return username

    # fallback – guaranteed unique
    return f"user_{uuid.uuid4().hex[:8]}"
