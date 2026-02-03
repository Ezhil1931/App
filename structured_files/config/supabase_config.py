
#------------------------------------
# This for supabase native package  connection code 
#------------------------------------

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

#------------------------------------
# This for sqlqclhemy connection code 
#------------------------------------

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

