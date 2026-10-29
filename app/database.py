import os
from pymongo import MongoClient
import mongomock

_client = None

def get_db():
    global _client
    if _client is None:
        use_mock = os.getenv("USE_MONGOMOCK", "false").lower() in ("true", "1")
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DB_NAME", "home_storage_db")

        if use_mock:
            _client = mongomock.MongoClient()
        else:
            try:
                client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=2000)
                client.admin.command('ping')
                _client = client
            except Exception:
                _client = mongomock.MongoClient()

    db_name = os.getenv("MONGODB_DB_NAME", "home_storage_db")
    return _client[db_name]

def reset_db_client():
    global _client
    _client = None
