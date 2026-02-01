from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import sys
import urllib.parse

variations = [
    ("Shop", "shop123456"),
    ("shop", "shop123456"),
    ("Shop", "Shop123456"),
    ("shop", "Shop123456"),
    ("Shop", "shop12345"),
    ("shop", "shop12345"),
]

def test_connection():
    print("Starting MongoDB connection diagnostics...")
    print("-" * 40)
    
    for user, password in variations:
        encoded_user = urllib.parse.quote_plus(user)
        encoded_pass = urllib.parse.quote_plus(password)
        
        # Try both atlas-style and standard-style URIs if needed
        # For now sticking to the provided Atlas SRV format
        uri = f"mongodb+srv://{encoded_user}:{encoded_pass}@shop.xtmkurh.mongodb.net/?appName=Shop"
        
        print(f"Testing {user}:***...")
        try:
            client = MongoClient(uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)
            # Send a ping to confirm a successful connection
            client.admin.command('ping')
            print(f"  ==> SUCCESS with {user}:{password}")
            
            # List databases to see what's there
            db_names = client.list_database_names()
            print(f"  ==> Available databases: {db_names}")
            
            # Return the working URI
            return uri
            
        except Exception as e:
            print(f"  ==> Failed: {str(e)}")
            continue

    print("-" * 40)
    print("All provided variations failed.")
    return None

if __name__ == "__main__":
    working_uri = test_connection()
    if not working_uri:
        sys.exit(1)
