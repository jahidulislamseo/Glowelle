import os
from pymongo import MongoClient
from decouple import config
from django.conf import settings

class MongoDBClient:
    """
    A singleton-like helper for MongoDB Atlas connections.
    """
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            uri = config('MONGODB_URI', default=None)
            if not uri:
                # Fallback if not in .env
                return None
            
            try:
                cls._client = MongoClient(uri)
                # Test connection briefly
                cls._client.admin.command('ping')
            except Exception as e:
                print(f"MongoDB connection error: {e}")
                cls._client = None
        return cls._instance

    def get_client(self):
        return self._client

    def get_database(self, db_name="shop_db"):
        if self._client:
            return self._client[db_name]
        return None

def get_mongodb_db(db_name="shop_db"):
    """
    Shortcut function to get a specific MongoDB database.
    """
    client_instance = MongoDBClient()
    if client_instance:
        return client_instance.get_database(db_name)
    return None
