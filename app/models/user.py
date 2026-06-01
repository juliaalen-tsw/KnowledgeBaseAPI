"""
models/user.py
--------------
The User database model.

SQLAlchemy models describe the structure of database tables.
Each attribute decorated with 'mapped_column' becomes a column in the table.

Think of this like a TypeScript interface PLUS the database schema definition
combined into one class.
"""

from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import String, Enum as SAEnum, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, Enum):
    """
    Python Enum for user roles.
    Using str as a base means UserRole.MEMBER == "MEMBER" is True.
    This makes serialization (converting to JSON) simpler.
    """
    MEMBER = "MEMBER"
    ADMIN = "ADMIN"


class User(Base):
    """
    Represents the 'users' table in PostgreSQL.
    
    Relationships:
    - One user -> many articles (author)
    - One user -> many comments
    - One user -> many bookmarks
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="userrole"),
        default=UserRole.MEMBER,
        nullable=False
    )
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()  # The database sets this automatically
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()  # Automatically updated when the row changes
    )

    # Relationships - these tell SQLAlchemy how tables are connected.
    # 'back_populates' creates a two-way link between models.
    articles: Mapped[list["Article"]] = relationship("Article", back_populates="author")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="author")
    bookmarks: Mapped[list["Bookmark"]] = relationship("Bookmark", back_populates="user")
