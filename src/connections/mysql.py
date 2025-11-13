from mysql.connector import Error as MySQLError
import mysql.connector

def connect_mysql(host, user, password, database=None, port=3306):
    """
    Connect to MySQL database.

    Args:
        host: MySQL server hostname or IP address
        user: MySQL username
        password: MySQL password
        database: Database name (optional, can be None for initial connection)
        port: MySQL port (default: 3306)

    Returns:
        mysql.connector.connection object or error string
    """
    try:
        conn = mysql.connector.connect(
            host=host, user=user, password=password, database=database, port=port
        )
        conn.ping(reconnect=True)
        return conn
    except MySQLError as e:
        return f"MySQL Connection Error: {e}"
