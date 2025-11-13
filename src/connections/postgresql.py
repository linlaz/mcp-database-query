import psycopg2
from psycopg2 import OperationalError

def connect_postgres(host, user, password, database=None, port=5432):
    """
    Connect to PostgreSQL database.

    Args:
        host: PostgreSQL server hostname or IP address
        user: PostgreSQL username
        password: PostgreSQL password
        database: Database name (optional, defaults to 'postgres' if None)
        port: PostgreSQL port (default: 5432)

    Returns:
        psycopg2.connection object or error string
    """
    try:
        conn = psycopg2.connect(
            host=host, user=user, password=password, dbname=database, port=port
        )
        return conn
    except OperationalError as e:
        return f"PostgreSQL Connection Error: {e}"
