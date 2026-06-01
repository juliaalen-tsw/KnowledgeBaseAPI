from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    parent_id: int | None = None  # If set, this is a reply


class CommentResponse(BaseModel):
    id: int
    content: str
    article_id: int
    author: UserResponse
    parent_id: int | None
    replies: list["CommentResponse"] = []  # Nested replies
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Required for self-referencing models in Pydantic
CommentResponse.model_rebuild()
