from pymongo.errors import PyMongoError
from pymongo import MongoClient
from urllib.parse import quote_plus


def connect_mongo(host, user, password, database=None, port=27017):
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

        return client

    except PyMongoError as e:
        return f"MongoDB Connection Error: {e}"
    except Exception as e:
        return f"Connection Error: {e}"
