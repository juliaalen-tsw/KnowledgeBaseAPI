from datetime import datetime
from pydantic import BaseModel
from app.schemas.article import ArticleListResponse


class BookmarkResponse(BaseModel):
    id: int
    article: ArticleListResponse
    created_at: datetime
    bookmarked: bool = True

    model_config = {"from_attributes": True}


class BookmarkToggleResponse(BaseModel):
    bookmarked: bool
    message: str
