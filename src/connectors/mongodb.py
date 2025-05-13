from pymongo import MongoClient
from bson import json_util

class MongoDBConnector:
    def __init__(self, uri, database):
        self.client = MongoClient(uri)
        self.db = self.client[database]

    def fetch_all(self, collection_name):
        """
        Fetch all documents from a MongoDB collection.
        Returns a list of documents, with ObjectId converted to strings.
        """
        try:
            collection = self.db[collection_name]
            documents = list(collection.find())
            # Convert MongoDB documents to JSON-compatible format
            return json_util.dumps(documents, default=json_util.default)
        except Exception as e:
            print(f"Error fetching data from MongoDB collection {collection_name}: {e}")
            return []

    def get_change_stream(self, collection_name):
        """
        Get a Change Stream cursor for a MongoDB collection.
        """
        try:
            collection = self.db[collection_name]
            return collection.watch(full_document='updateLookup')
        except Exception as e:
            print(f"Error setting up Change Stream for collection {collection_name}: {e}")
            raise

    def close(self):
        """Close the MongoDB10 MongoDB connection."""
        self.client.close()