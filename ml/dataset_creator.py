"""
dataset_creator.py

This module contains functions for extracting Reddit data from a database and creating datasets.
The dataset is saved in both pickle and CSV formats.

Functions:
- fetch_data_by_flairs: Fetches Reddit posts filtered by specific flairs and date range and saves the dataset.

Author:
- Erik Pereira
"""

import os
import sys
import pandas as pd
import pickle
import argparse

from sqlalchemy import select, MetaData, Table, and_
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from DB import database_engine

def fetch_data_by_flairs(engine, table, date_start, date_end, dataset_name):
    """
    Fetches Reddit posts filtered by specific flairs and date range and saves the dataset.

    Args:
        engine (sqlalchemy.engine.Engine): SQLAlchemy engine connected to the database.
        table (str): Name of the table containing Reddit data.
        date_start (str): Start date in YYYY-MM format.
        date_end (str): End date in YYYY-MM format.
        dataset_name (str): Name of the dataset file (without extension).

    Returns:
        pandas.DataFrame: DataFrame containing the text and label of the posts.
    """
    metadata = MetaData()
    submissions = Table(table, metadata, autoload_with=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    flairs = [
        'Need Support',
        'Venting',
        'Opinion / Thoughts',
        'Sadness / Grief',
        'Good News / Happy',
        'Inspiration / Encouragement',
        'Resources',
        'Research Study'
    ]

    query = select(
        submissions.c.title,
        submissions.c.selftext,
        submissions.c.link_flair_text.label('label_post')
    ).where(
        and_(
            submissions.c.link_flair_text.in_(flairs),
            submissions.c.subreddit == 'mentalhealth',
            submissions.c.created_utc > date_start,
            submissions.c.created_utc < date_end,
            submissions.c.selftext != '[deleted]',
            submissions.c.selftext != '[removed]'
        )
    )

    result = session.execute(query).fetchall()

    df = pd.DataFrame(result, columns=['title', 'selftext', 'label_post'])
    df['text'] = df['title'].fillna('') + " " + df['selftext'].fillna('')

    # Save the dataset in pickle format
    pickle_dir = "data/datasets/pickle"
    os.makedirs(pickle_dir, exist_ok=True)
    pickle_path = os.path.join(pickle_dir, f"{dataset_name}_raw.pkl")
    with open(pickle_path, "wb") as pickle_file:
        pickle.dump(df[['text', 'label_post']], pickle_file)
    print(f"Dataset saved in pickle format at: {pickle_path}")

    # Save the dataset in CSV format
    csv_dir = "data/datasets/csv"
    os.makedirs(csv_dir, exist_ok=True)
    csv_path = os.path.join(csv_dir, f"{dataset_name}_raw.csv")
    df[['text', 'label_post']].to_csv(csv_path, index=False)
    print(f"Dataset saved in CSV format at: {csv_path}")

    return df[['text', 'label_post']]

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extrae datos de Reddit por flairs y fechas.")
    parser.add_argument("--database", type=str, required=True, help="Nombre de la base de datos.")
    parser.add_argument("--table", type=str, required=True, help="Nombre de la tabla.")
    parser.add_argument("--start_date", type=str, required=True, help="Fecha de inicio en formato YYYY-MM.")
    parser.add_argument("--end_date", type=str, required=True, help="Fecha de fin en formato YYYY-MM.")
    parser.add_argument("--dataset_name", type=str, default="dataset_flairs", help="Nombre del dataset.")

    args = parser.parse_args()
    engine = database_engine(args.database)
    df = fetch_data_by_flairs(engine, args.table, args.start_date, args.end_date, args.dataset_name)
    print(df.head())
