
from supabase import create_client,Client

import os
from dotenv import load_dotenv

# Load .env file (for local development)
load_dotenv()

# API Keys
API_KEY = os.getenv("api_key_bypass")


# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Optional: sanity check




supabase:Client = create_client(SUPABASE_URL,API_KEY)
