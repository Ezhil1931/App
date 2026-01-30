from pathlib import Path

# Get ROOT directory of the project
ROOT_DIR = Path(__file__).resolve().parents[2]

PRIVATE_KEY_PATH = ROOT_DIR / "private.pem"
PUBLIC_KEY_PATH = ROOT_DIR / "public.pem"

with open(PRIVATE_KEY_PATH, "r") as f:
    PRIVATE_KEY = f.read()

with open(PUBLIC_KEY_PATH, "r") as f:
    PUBLIC_KEY = f.read()

ALGORITHM = "RS256"
