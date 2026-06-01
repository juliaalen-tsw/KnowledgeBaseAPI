"""
routers/comments.py
-------------------
Comment endpoints - nested under article slugs.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.services import comment_service

router = APIRouter(tags=["Comments"])


@router.get(
    "/articles/{slug}/comments",
    response_model=list[CommentResponse],
    summary="List comments for an article (with nested replies)",
)
async def list_comments(slug: str, db: AsyncSession = Depends(get_db)):
    """
    Get all top-level comments for a published article.
    Each comment includes its replies nested inside it.
    """
    return await comment_service.get_article_comments(slug, db)


@router.post(
    "/articles/{slug}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to an article",
)
async def create_comment(
    slug: str,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Post a comment on an article.
    Set `parent_id` to reply to an existing comment.
    Only one level of nesting is supported (replies to replies are rejected).
    """
    return await comment_service.create_comment(slug, data, current_user, db)


@router.delete(
    "/articles/{slug}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment (author or admin only)",
)
async def delete_comment(
    slug: str,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a comment. Only the comment author or an admin can do this."""
    await comment_service.delete_comment(slug, comment_id, current_user, db)
