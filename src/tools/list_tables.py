from fastmcp import FastMCP
from src.helpers.mysql_excecute import mysql_list_tables
from src.helpers.postgresql_execute import postgresql_list_tables
from src.helpers.mongodb_excecute import mongodb_list_tables

list_tables_mcp = FastMCP()


@list_tables_mcp.tool()
def list_tables(
    engine: str,
):
    """
    List all tables (MySQL/PostgreSQL) or collections (MongoDB) in a specific database.

    Parameters:
    -----------
    engine : str
        Database engine type. Valid values: "mysql", "postgres", "mongo"

    Returns:
    --------
    str
        Formatted string containing list of table/collection names, or error message

    Example Usage:
    --------------
    MySQL:
        list_tables("mysql")

    PostgreSQL:
        list_tables("postgres")

    MongoDB:
        list_tables("mongo")
        list_tables("mongo")
    """
    match engine:
        case "mysql":
            return mysql_list_tables()
        case "postgres":
            return postgresql_list_tables()
        case "mongo":
            return mongodb_list_tables()
        case _:
            return f"Error: Unsupported database engine '{engine}'. Supported engines are: mysql, postgres, mongo."
