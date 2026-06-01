"""
models/tag.py
-------------
Tags are simple labels (e.g., "python", "docker", "fastapi").
They have a many-to-many relationship with articles.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.article import article_tags


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)

    # The 'secondary' argument points to the join table defined in article.py
    articles: Mapped[list["Article"]] = relationship(
        "Article", secondary=article_tags, back_populates="tags"
    )
