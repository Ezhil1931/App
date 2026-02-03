from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from ..config.supabase_config import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, index=True)
    user_email = Column(String, unique=True, index=True, nullable=False)
    user_name = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    refer_id = Column(String)
    otp = Column(String)
    otp_expiry = Column(DateTime)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    modified_by = Column(String)
