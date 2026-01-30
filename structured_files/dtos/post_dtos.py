from pydantic import BaseModel
from uuid import UUID

class UpdatePostPayload(BaseModel):
    post_id: UUID
    caption: str

class DeletePostPayload(BaseModel):
    post_id: UUID
