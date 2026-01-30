
from supabase import create_client, Client

import os
from dotenv import load_dotenv

# Load .env file (for local development)
load_dotenv()

# API Keys
API_KEY = os.getenv("api_key_bypass")


# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Optional: sanity check
required_vars = ["API_KEY","SUPABASE_URL"]
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Environment variable {var} is not set!")




supabase:Client = create_client(SUPABASE_URL,API_KEY)
