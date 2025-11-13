from fastmcp import FastMCP
from src.helpers.mysql_excecute import mysql_describe_table
from src.helpers.postgresql_execute import postgresql_describe_table
from src.helpers.mongodb_excecute import mongodb_describe_tables

describe_table_mcp = FastMCP()


@describe_table_mcp.tool()
def describe_table(
    engine: str,
    table: str,
):
    """
    Describe table structure (columns, types, constraints) or MongoDB collection schema.

    Parameters:
    -----------
    engine : str
        Database engine type. Valid values: "mysql", "postgres", "mongo"

    table : str
        Table name (MySQL/PostgreSQL) or collection name (MongoDB) to describe
        Examples: "users", "customers", "orders"

    Returns:
    --------
    str
        Table structure information:

        MySQL:
            Column details including: Field, Type, Null, Key, Default, Extra
            Format: Tabular output from DESCRIBE command

        PostgreSQL:
            Column details including: column_name, data_type, is_nullable, column_default
            Format: Tabular output from information_schema

        MongoDB:
            Sample document structure with field names and inferred types
            Based on first document in collection
            Shows: field path, data type, sample value

    Example Usage:
    --------------
    MySQL:
        describe_table("mysql", "users")
        Output:
            Field       | Type         | Null | Key | Default | Extra
            id          | int(11)      | NO   | PRI | NULL    | auto_increment
            username    | varchar(50)  | NO   | UNI | NULL    |
            email       | varchar(100) | YES  |     | NULL    |
            created_at  | timestamp    | YES  |     | CURRENT_TIMESTAMP |

    PostgreSQL:
        describe_table("postgres", "products")
        Output:
            column_name | data_type          | is_nullable | column_default
            id          | integer            | NO          | nextval('products_id_seq')
            name        | character varying  | NO          |
            price       | numeric            | YES         | 0
            created_at  | timestamp          | YES         | now()

    MongoDB:
        describe_table("mongo", "users")
        describe_table("mongo", "customers")
        Output:
            Field Structure of 'users' collection:

            _id: ObjectId (507f1f77bcf86cd799439011)
            username: string (john_doe)
            email: string (john@example.com)
            age: number (25)
            status: string (active)
            created_at: date (2024-01-15T10:30:00Z)
            profile: object
              profile.name: string (John Doe)
              profile.avatar: string (https://...)
            tags: array
              tags[0]: string (premium)

    Notes:
    ------
    - For MongoDB, this samples ONE document to infer schema
    - MongoDB collections can have varying schemas per document
    - For more accurate MongoDB schema, query multiple documents
    - Empty collections will return "No documents found" message
    """

    match engine:
        case "mysql":
            return mysql_describe_table(table)
        case "postgres":
            return postgresql_describe_table(table)
        case "mongo":
            return mongodb_describe_tables(table)
        case _:
            return "Error: Unknown engine. Use: mysql | postgres | mongo"
