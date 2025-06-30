"""
connect.py

This module provides utility functions for connecting to a MySQL database using SQLAlchemy.
It includes functions to create a database session and engine for interacting with the database.

Functions:
- database_connect: Establishes a connection to the database and returns a session object.
- database_engine: Establishes a connection to the database and returns an engine object.

Author:
- Erik Pereira
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

def database_connect(database_name: str):
    """
    Establishes a connection to the MySQL database and returns a session object.

    Args:
        database_name (str): Name of the database to connect to.

    Returns:
        sqlalchemy.orm.Session: A SQLAlchemy session object for interacting with the database.

    Example:
        session = database_connect("reddit_db")
    """
    # Create the SQLAlchemy engine for the specified database
    engine = create_engine(
        f"mysql+mysqlconnector://root:root@localhost:3306/{database_name}?charset=utf8mb4"
    )

    # Create a session factory bound to the engine
    Session = sessionmaker(bind=engine, autoflush=False)

    # Return a session instance
    return Session()

def database_engine(database_name: str):
    """
    Establishes a connection to the MySQL database and returns an engine object.

    Args:
        database_name (str): Name of the database to connect to.

    Returns:
        sqlalchemy.engine.Engine: A SQLAlchemy engine object for interacting with the database.

    Example:
        engine = database_engine("reddit_db")
    """
    # Create the SQLAlchemy engine for the specified database
    engine = create_engine(
        f"mysql+mysqlconnector://root:root@localhost:3306/{database_name}?charset=utf8mb4"
    )

    # Return the engine instance
    return engine