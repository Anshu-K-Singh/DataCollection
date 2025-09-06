import json
from bson import json_util
from src.connectors.mongodb import MongoDBConnector
from src.connectors.postgresql import PostgreSQLConnector
from src.utils.json_manager import JSONManager

class DataFetcher:
    """A class to fetch data from databases and save it to JSON files."""

    def __init__(self, mongo_conn: MongoDBConnector, pg_conn: PostgreSQLConnector, json_manager: JSONManager):
        """Initializes the DataFetcher.

        Args:
            mongo_conn (MongoDBConnector): An instance of MongoDBConnector.
            pg_conn (PostgreSQLConnector): An instance of PostgreSQLConnector.
            json_manager (JSONManager): An instance of JSONManager.
        """
        self.mongo_conn = mongo_conn
        self.pg_conn = pg_conn
        self.json_manager = json_manager

    def fetch_and_save_mongo(self, collection_name: str):
        """Fetches data from a MongoDB collection and saves it to a JSON file.

        The data is fetched from the specified collection, parsed, and then
        written to a JSON file named after the collection.

        Args:
            collection_name (str): The name of the MongoDB collection to fetch from.
        """
        data = self.mongo_conn.fetch_all(collection_name)
        if data:
            # Parse MongoDB JSON string to Python object
            parsed_data = json.loads(data, object_hook=json_util.object_hook)
            self.json_manager.write_json(collection_name, parsed_data)

    def fetch_and_save_postgres(self, table_name: str):
        """Fetches data from a PostgreSQL table and saves it to a JSON file.

        The data is fetched from the specified table and then written to a
        JSON file named after the table.

        Args:
            table_name (str): The name of the PostgreSQL table to fetch from.
        """
        data = self.pg_conn.fetch_all(table_name)
        if data:
            self.json_manager.write_json(table_name, data)