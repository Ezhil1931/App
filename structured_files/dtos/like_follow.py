from pydantic import BaseModel
from uuid import UUID


#payload for like and follow

class PostLikePayload(BaseModel):
    post_id: UUID

class LikeRequest(PostLikePayload):
    pass


class FollowPayload(BaseModel):
    following_id: str 
