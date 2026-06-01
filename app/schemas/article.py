"""
schemas/article.py
------------------
Pydantic schemas for Article endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from app.models.article import ArticleStatus
from app.schemas.user import UserResponse
from app.schemas.tag import TagResponse


class ArticleCreate(BaseModel):
    """Data required to create a new article."""
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=280)
    status: ArticleStatus = ArticleStatus.DRAFT
    tag_ids: list[int] = Field(default_factory=list)


class ArticleUpdate(BaseModel):
    """All fields are optional - only send what you want to change."""
    title: str | None = Field(default=None, max_length=300)
    content: str | None = None
    summary: str | None = Field(default=None, max_length=280)
    status: ArticleStatus | None = None
    tag_ids: list[int] | None = None


class ArticleResponse(BaseModel):
    """Full article response including author and tags."""
    id: int
    title: str
    slug: str
    content: str
    summary: str | None
    author: UserResponse
    status: ArticleStatus
    is_featured: bool
    view_count: int
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tags: list[TagResponse] = []

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    """Lightweight response for list endpoints (no full content)."""
    id: int
    title: str
    slug: str
    summary: str | None
    author: UserResponse
    status: ArticleStatus
    is_featured: bool
    view_count: int
    published_at: datetime | None
    created_at: datetime
    tags: list[TagResponse] = []

    model_config = {"from_attributes": True}


class PaginatedArticles(BaseModel):
    """Wraps a list of articles with pagination metadata."""
    items: list[ArticleListResponse]
    total: int
    page: int
    per_page: int
    pages: int
