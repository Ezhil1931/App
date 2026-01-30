import uuid
from ..config.supabase_config import supabase


def generate_unique_username() -> str:
    """
    Generates a unique username like: user_482193
    Ensures no conflict in DB.
    """

    MAX_ATTEMPTS = 10

    for _ in range(MAX_ATTEMPTS):
        username = f"user_{uuid.uuid4().hex[:6]}"

        exists = (
            supabase
            .table("users")
            .select("user_id")
            .eq("user_name", username)
            .execute()
            .data
        )

        if not exists:
            return username

    # Fallback (almost impossible to reach)
    return f"user_{uuid.uuid4().hex}"
