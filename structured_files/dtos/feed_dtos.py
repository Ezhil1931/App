from pydantic import BaseModel
from typing import List, Optional

class FeedRequestDto(BaseModel):
    skip: int = 0
    limit: int = 15

class PostImageDto(BaseModel):
    image_url: str
    position: int

class PostDto(BaseModel):
    post_id: str
    post_title: Optional[str]
    post_content: Optional[str]
    user_name: str
    full_name: Optional[str]
    profile_img_url: Optional[str]
    category_text: Optional[str]
    total_likes: int
    liked_by_me: bool
    comments_count: int
    created_at: str
    owned_by_me: bool
    images: List[PostImageDto]

class FeedResponseDto(BaseModel):
    status: str
    posts: List[PostDto]
    auth_token: str
    refresh_token: str
