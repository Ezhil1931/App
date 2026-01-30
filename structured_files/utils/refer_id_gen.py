import random
from ..config.supabase_config import supabase

SAFE_LETTERS = "ABCDEFGHJKMNPQRSTUVWXYZ"
SAFE_NUMBERS = "23456789"

MAX_ATTEMPTS = 5


def _generate_candidate() -> str:
    """
    Generate a refer_id using one of the allowed patterns:
    - 4 letters + 2 numbers
    - 3 letters + 3 numbers
    - 5 letters + 1 number
    """
    pattern = random.choice([
        (4, 2),  # LLLLNN
        (3, 3),  # LLLNNN
        (5, 1),  # LLLLLN
    ])

    letters_count, numbers_count = pattern

    letters = "".join(random.choice(SAFE_LETTERS) for _ in range(letters_count))
    numbers = "".join(random.choice(SAFE_NUMBERS) for _ in range(numbers_count))

    return letters + numbers


def generate_referral_id() -> str:
    """
    Generates a unique refer_id with DB check and safety fallback.
    """
    for _ in range(MAX_ATTEMPTS):
        refer_id = _generate_candidate()

        exists = (
            supabase.table("users")
            .select("user_id")
            .eq("refer_id", refer_id)
            .limit(1)
            .execute()
        )

        if not exists.data:
            return refer_id

    # 🔐 Safety fallback (extremely rare)
    raise RuntimeError("Failed to generate unique refer_id after multiple attempts")
