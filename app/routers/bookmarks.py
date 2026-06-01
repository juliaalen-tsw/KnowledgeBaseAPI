"""
routers/bookmarks.py
--------------------
Bookmark endpoints for saving/unsaving articles.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.bookmark import BookmarkToggleResponse
from app.schemas.article import ArticleListResponse
from app.services import bookmark_service

router = APIRouter(tags=["Bookmarks"])


@router.post(
    "/articles/{slug}/bookmark",
    response_model=BookmarkToggleResponse,
    summary="Toggle bookmark (add/remove)",
)
async def toggle_bookmark(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add or remove a bookmark on an article.
    - If not bookmarked -> adds bookmark, returns `bookmarked: true`
    - If already bookmarked -> removes it, returns `bookmarked: false`
    """
    result = await bookmark_service.toggle_bookmark(slug, current_user, db)
    return result


@router.get(
    "/bookmarks/my",
    response_model=list[ArticleListResponse],
    summary="List my bookmarked articles",
)
async def my_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all articles bookmarked by the current user."""
    bookmarks = await bookmark_service.get_my_bookmarks(current_user, db)
    # Extract the article from each bookmark and return it
    return [ArticleListResponse.model_validate(bm.article) for bm in bookmarks]
