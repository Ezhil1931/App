from pydantic import BaseModel, HttpUrl
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class PostImageResponse(BaseModel):
    image_url: HttpUrl
    order_index: int

class PostResponse(BaseModel):
    post_id: UUID
    user_id: UUID
    caption: Optional[str]
    created_at: datetime
    images: List[PostImageResponse] = []
