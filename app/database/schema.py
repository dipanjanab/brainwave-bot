from contextlib import closing
from app.database.connection import connect


CREATE_STORIES_TABLE = """
CREATE TABLE IF NOT EXISTS stories (
    story_id INTEGER PRIMARY KEY,
    story_title TEXT NOT NULL,
    market TEXT NOT NULL CHECK (market IN ('NEMIA', 'APAC', 'AMER', 'LATAM')),
    category TEXT NOT NULL,
    submission_date TEXT NOT NULL,
    status TEXT NOT NULL,
    submitter TEXT NOT NULL,
    revenue REAL NOT NULL CHECK (revenue >= 0)
)
"""


def create_database() -> None:
    with closing(connect()) as connection:
        connection.execute(CREATE_STORIES_TABLE)


if __name__ == "__main__":
    create_database()
    print("Brainwave database created.")
