"""
process.py

This module provides functions for processing Reddit data files, extracting comments, and saving matched records to a database.
It includes functionality for handling file processing, interacting with the Reddit API, and managing database connections.

Functions:
- get_reddit_comments: Fetches comments for a given Reddit post using the Reddit API.
- process_file: Processes a file by filtering records based on specific criteria and saving matched records to a database.

Requirements:
- Python 3.6 or higher.
- Libraries: json, time, requests, random, datetime, logging, praw.
- Dependencies: FileHandle, Submission, Comment, database_connect.

Author:
- Erik Pereira
"""

import json
import time
import requests
import random
from utils import FileHandle
from models import Submission, Comment
from datetime import datetime
from DB import database_connect
import logging
import praw

# Logger setup
log = logging.getLogger("log")

# Reddit API setup
reddit = praw.Reddit(
    client_id="QC4LbDNEHL0O_nty-4EjjA",
    client_secret="oofTnK8zmDCqjzlOo8Canim4P8f8zQ",
    user_agent="python:mentalhealthbot:v1.0.0 (by /u/Parking_Limit6943), created to collect data for research purposes on mental health subreddits."
)

def get_reddit_comments(post_id, max_retries=6):
    """
    Fetches comments for a given Reddit post using the Reddit API.

    Args:
        post_id (str): The ID of the Reddit post.
        max_retries (int, optional): Maximum number of retries for API requests. Defaults to 6.

    Returns:
        list: A list of Comment objects extracted from the post.

    Example:
        comments = get_reddit_comments("post_id")
    """
    url = f"https://www.reddit.com/comments/{post_id}.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    wait_time = 2  # Initial wait time for retries

    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            break  # Success, exit the loop

        elif response.status_code == 429:
            log.warning(f"429 Too Many Requests. Waiting {wait_time}s before retrying...")
            time.sleep(wait_time + random.uniform(0, 1))  # Add a small random delay
            wait_time *= 2  # Exponentially increase wait time

        else:
            log.error(f"Error {response.status_code} while fetching comments for post {post_id}")
            return []

    if response.status_code != 200:
        log.error("Too many failed attempts. Skipping post.")
        return []

    data = response.json()
    comments = []

    # Recursive function to extract comments and nested replies
    def extract_comments(comment_list, parent_id=None, depth=0):
        for comment in comment_list:
            if "body" in comment["data"] and comment["data"]["author"] != "AutoModerator":  # Skip elements without text
                comments.append(Comment(
                    id=comment["data"]["id"],
                    post_id=post_id,
                    parent_id=parent_id,
                    author=f"u/{comment['data']['author']}" if comment["data"]["author"] != "[deleted]" else "[deleted]",
                    created_utc=datetime.utcfromtimestamp(comment["data"]["created_utc"]) if comment["data"]["created_utc"] else None,
                    body=comment["data"]["body"],
                    depth=depth
                ))

                # Process replies recursively if available
                if "replies" in comment["data"] and isinstance(comment["data"]["replies"], dict):
                    extract_comments(comment["data"]["replies"]["data"]["children"], parent_id=comment["data"]["id"], depth=depth + 1)

    # Extract top-level comments
    extract_comments(data[1]["data"]["children"], parent_id=post_id)

    log.info(f"Extracted {len(comments)} comments for post {post_id}")

    return comments

def process_file(file, queue, field, values, database_name, comment_depth):
    """
    Processes a file by iterating through its lines and writing out the ones where the `field` of the object matches `value`.
    Also passes status information back to the parent via a queue.

    Args:
        file (FileConfig): The file configuration object containing input and output paths.
        queue (Queue): The queue to pass status information back to the parent process.
        field (str): The field of the object to match against the values.
        values (list): The list of values to match against the field.
        database_name (str): Name of the database to save matched records.
        comment_depth (int): Maximum depth of comments to process (-1 for no comments, 0 for direct comments, etc.).

    Returns:
        None

    Example:
        process_file(file, queue, "subreddit", ["mentalhealth"], "reddit_db", 0)
    """
    queue.put(file)
    input_handle = FileHandle(file.input_path)
    session = database_connect(database_name)

    matched_records = []
    comment_records = []
    batch_size = 20

    value = None
    if len(values) == 1:
        value = min(values)

    try:
        for line, file_bytes_processed in input_handle.yield_lines():
            try:
                obj = json.loads(line)
                matched = False
                observed = obj[field].lower()

                # Check if the field matches the value
                if value is not None:
                    if value == observed or value in observed:
                        matched = True

                if matched:
                    matched_records.append(Submission(
                        id=obj.get("id"),
                        author=f"u/{obj.get('author')}" if obj.get("author") else None,
                        title=obj.get("title"),
                        created_utc=datetime.utcfromtimestamp(int(obj.get("created_utc"))) if obj.get("created_utc") else None,
                        selftext=obj.get("selftext", ""),
                        subreddit=obj.get("subreddit"),
                        link_flair_text=obj.get("link_flair_text"),
                        link=f"https://www.reddit.com{obj.get('permalink')}" if obj.get("permalink") else None,
                        num_comments=obj.get("num_comments"),
                        score=obj.get("score"),
                    ))

                    # Fetch comments if comment depth is specified
                    if comment_depth >= 0:
                        comments = get_reddit_comments(obj.get("id"))
                        comment_records.extend(comments)

                    file.lines_matched += 1

                # Save records to the database in batches
                if len(matched_records) >= batch_size:
                    session.bulk_save_objects(matched_records)
                    if comment_records:
                        session.bulk_save_objects(comment_records)
                    session.commit()
                    matched_records = []  # Reset list
                    comment_records = []  # Reset list
                    log.info("DB insert completed")

            except (KeyError, json.JSONDecodeError, AttributeError) as err:
                file.error_lines += 1

            file.lines_processed += 1
            if file.lines_processed % 1000000 == 0:
                file.bytes_processed = file_bytes_processed
                queue.put(file)

        # Save remaining records
        if matched_records:
            session.bulk_save_objects(matched_records, preserve_order=True)
            session.commit()
        if comment_records:
            session.bulk_save_objects(comment_records, preserve_order=True)
            session.commit()

        session.close()
        file.complete = True
        file.bytes_processed = file.file_size

    except Exception as err:
        file.error_message = str(err)

    queue.put(file)