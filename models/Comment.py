"""
Comment.py

This module defines the Comment model, which represents Reddit comment data stored in a database.
The model is built using SQLAlchemy and maps the fields of a Reddit comment to a database table.

Classes:
- Comment: SQLAlchemy model for the "comments" table.

Author:
- Erik Pereira
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Base class for SQLAlchemy models
Base = declarative_base()

class Comment(Base):
    """
    SQLAlchemy model for the "comments" table.

    Attributes:
        id (str): Unique identifier for the comment (primary key).
        post_id (str): ID of the Reddit post the comment belongs to.
        parent_id (str): ID of the parent comment or post.
        author (str): Author of the comment.
        created_utc (datetime): UTC timestamp when the comment was created.
        body (str): Text content of the comment.
        depth (int): Depth of the comment in the thread hierarchy.
    """
    __tablename__ = "comments"
    id = Column(String(255), primary_key=True)  # Unique identifier for the comment
    post_id = Column(String(255))  # ID of the Reddit post the comment belongs to
    parent_id = Column(String(255))  # ID of the parent comment or post
    author = Column(String(255))  # Author of the comment
    created_utc = Column(DateTime)  # UTC timestamp of comment creation
    body = Column(Text)  # Text content of the comment
    depth = Column(Integer)  # Depth of the comment in the thread hierarchy
    
    def __repr__(self):
        """
        Returns a string representation of the Comment instance.

        Returns:
            str: String representation of the Comment instance.
        """
        return (f"Comment(id={self.id}, post_id={self.post_id}, parent_id={self.parent_id}, "
                f"author={self.author}, created_utc={self.created_utc}, body={self.body}, depth={self.depth})")