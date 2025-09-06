from pymongo import MongoClient
from bson import json_util

class MongoDBConnector:
    """A connector class for interacting with a MongoDB database."""

    def __init__(self, uri, database):
        """Initializes the MongoDBConnector.

        Args:
            uri (str): The MongoDB connection URI.
            database (str): The name of the database to connect to.
        """
        self.client = MongoClient(uri)
        self.db = self.client[database]

    def fetch_all(self, collection_name):
        """Fetches all documents from a specified MongoDB collection.

        Args:
            collection_name (str): The name of the collection to fetch from.

        Returns:
            str: A JSON string representing the list of documents.
                 Returns an empty list as a JSON string if an error occurs.
        """
        try:
            collection = self.db[collection_name]
            documents = list(collection.find())
            # Convert MongoDB documents to JSON-compatible format
            return json_util.dumps(documents, default=json_util.default)
        except Exception as e:
            print(f"Error fetching data from MongoDB collection {collection_name}: {e}")
            return "[]"

    def get_change_stream(self, collection_name):
        """Gets a Change Stream cursor for a MongoDB collection.

        Change Streams allow applications to access real-time data changes
        without the complexity and risk of tailing the oplog.

        Args:
            collection_name (str): The name of the collection to monitor.

        Returns:
            pymongo.change_stream.ChangeStream: A ChangeStream cursor.

        Raises:
            Exception: If there is an error setting up the Change Stream.
        """
        try:
            collection = self.db[collection_name]
            return collection.watch(full_document='updateLookup')
        except Exception as e:
            print(f"Error setting up Change Stream for collection {collection_name}: {e}")
            raise

    def close(self):
        """Closes the MongoDB connection."""
        self.client.close()