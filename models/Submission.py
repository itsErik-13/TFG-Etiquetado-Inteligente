"""
Submission.py

This module defines the Submission model, which represents Reddit submission data stored in a database.
The model is built using SQLAlchemy and maps the fields of a Reddit submission to a database table.

Classes:
- Submission: SQLAlchemy model for the "submissions" table.

Author:
- Erik Pereira
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Base class for SQLAlchemy models
Base = declarative_base()

class Submission(Base):
    """
    SQLAlchemy model for the "submissions" table.

    Attributes:
        id (str): Unique identifier for the submission (primary key).
        author (str): Author of the submission.
        title (str): Title of the submission.
        created_utc (datetime): UTC timestamp when the submission was created.
        selftext (str): Text content of the submission.
        subreddit (str): Subreddit where the submission was posted.
        link_flair_text (str): Flair text associated with the submission.
        link (str): URL link to the submission.
        num_comments (int): Number of comments on the submission.
        score (int): Score of the submission (upvotes minus downvotes).
    """
    __tablename__ = "submissions"
    id = Column(String(255), primary_key=True)  # Unique identifier for the submission
    author = Column(String(255))  # Author of the submission
    title = Column(Text)  # Title of the submission
    created_utc = Column(DateTime)  # UTC timestamp of submission creation
    selftext = Column(Text)  # Text content of the submission
    subreddit = Column(String(255))  # Subreddit where the submission was posted
    link_flair_text = Column(String(255))  # Flair text associated with the submission
    link = Column(Text)  # URL link to the submission
    num_comments = Column(Integer)  # Number of comments on the submission
    score = Column(Integer)  # Score of the submission (upvotes minus downvotes)


