from fastmcp import FastMCP
from src.helpers.mysql_excecute import mysql_list_databases
from src.helpers.postgresql_execute import postgresql_list_databases
from src.helpers.mongodb_excecute import mongodb_list_databases

list_database_mcp = FastMCP()


@list_database_mcp.tool()
def list_databases(
    engine: str,
):
    """
    List all databases from MySQL, PostgreSQL, or MongoDB server.

    Parameters:
    -----------
    engine : str
        Database engine type. Valid values: "mysql", "postgres", "mongo"

    Returns:
    --------
    str
        Formatted string containing list of database names, or error message

    Example Usage:
    --------------
    MySQL:
        list_databases("mysql")

    PostgreSQL:
        list_databases("postgres")

    MongoDB:
        list_databases("mongo")
        list_databases("mongo")
    """

    match engine:
        case "mysql":
            return mysql_list_databases()
        case "postgres":
            return postgresql_list_databases()
        case "mongo":
            return mongodb_list_databases()
        case _:
            return "Error: Unknown engine. Use: mysql | postgres | mongo"
