from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class CommentPayload(BaseModel):
    post_id: UUID
    content: str
    parent_comment_id: Optional[UUID] = None

class PostCommentsRequest(BaseModel):
    post_id: UUID

class CommentRepliesRequest(BaseModel):
    comment_id: UUID

class DeleteCommentRequest(BaseModel):
    comment_id: UUID
