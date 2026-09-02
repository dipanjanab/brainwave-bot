from contextlib import closing
from app.database.connection import connect
from app.services.sql_validator import validate_sql


def run_read_only_sql(sql: str, parameters: tuple = ()) -> list[dict]:
    """Execute a validated parameterized read-only query."""
    query = validate_sql(sql)
    with closing(connect()) as connection:
        cursor = connection.execute(query, parameters)
        rows = [dict(row) for row in cursor.fetchall()]
    return rows
