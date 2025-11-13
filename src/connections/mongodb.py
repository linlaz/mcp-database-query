from pymongo.errors import PyMongoError
from pymongo import MongoClient

from urllib.parse import quote_plus

def connect_mongo(host, user, password, database=None, port=27017):
    """
    Connect to MongoDB database using the same format as MongoDB Compass.

    Args:
        host: MongoDB server hostname or IP address
        user: MongoDB username (will be URL-encoded automatically)
        password: MongoDB password (will be URL-encoded automatically)
        database: Database name for authentication and operations
        port: MongoDB port (default: 27017)
        auth_db: Authentication database (default: "admin")

    Connection String Format:
        mongodb://username:password@host:port/database?authMechanism=DEFAULT&directConnection=true

    Returns:
        pymongo.MongoClient object or error string

    Notes:
        - Uses directConnection=true for single server connection
        - Automatically URL-encodes username and password to handle special characters
        - Tests connection with ping command before returning
    """
    try:
        encoded_user = quote_plus(user)
        encoded_pass = quote_plus(password)

        uri = f"mongodb://{encoded_user}:{encoded_pass}@{host}:{port}/{database}?authMechanism=DEFAULT&directConnection=true"

        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            directConnection=True,
        )

        client[database].command("ping")
        return client

    except PyMongoError as e:
        return f"MongoDB Connection Error: {e}"
    except Exception as e:
        return f"Connection Error: {e}"
