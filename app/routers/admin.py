"""
routers/admin.py
----------------
Admin-only endpoints for platform management.
All routes here require the ADMIN role (enforced by get_current_admin dependency).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.dependencies.cache import get_cache, CacheService
from app.models.user import User, UserRole
from app.schemas.user import UserResponse
from app.schemas.article import ArticleResponse
from app.services import user_service, article_service
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])


class RoleUpdate(BaseModel):
    role: UserRole


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List all users (Admin only)",
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),  # _ prefix = used only for auth check
):
    """Get a list of all registered users."""
    return await user_service.get_all_users(db)


@router.patch(
    "/users/{user_id}/role",
    response_model=UserResponse,
    summary="Change a user's role (Admin only)",
)
async def change_user_role(
    user_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    """Promote a user to ADMIN or demote to MEMBER."""
    return await user_service.update_user_role(user_id, data.role, db)


@router.patch(
    "/articles/{slug}/feature",
    response_model=ArticleResponse,
    summary="Toggle featured status of an article (Admin only)",
)
async def toggle_featured(
    slug: str,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache),
    _admin: User = Depends(get_current_admin),
):
    """Toggle whether an article is featured (shown prominently)."""
    from app.dependencies.cache import article_detail_key
    article = await article_service.toggle_featured(slug, db)
    # Invalidate cache for this article
    await cache.delete(article_detail_key(slug))
    await cache.delete_pattern("articles:list:*")
    return ArticleResponse.model_validate(article)
