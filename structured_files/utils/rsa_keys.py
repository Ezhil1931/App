import os
from dotenv import load_dotenv

# Load .env file (for local development)
load_dotenv()

# Get keys from environment variables
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PUBLIC_KEY = os.getenv("PUBLIC_KEY")

ALGORITHM = "RS256"

# Optional: check if keys loaded correctly
