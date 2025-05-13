import json
from bson import json_util

class DataFetcher:
    def __init__(self, mongo_conn, pg_conn, json_manager):
        self.mongo_conn = mongo_conn
        self.pg_conn = pg_conn
        self.json_manager = json_manager

    def fetch_and_save_mongo(self, collection_name):
        """
        Fetch data from a MongoDB collection and save to JSON.
        """
        data = self.mongo_conn.fetch_all(collection_name)
        if data:
            # Parse MongoDB JSON string to Python object
            parsed_data = json.loads(data, object_hook=json_util.object_hook)
            self.json_manager.write_json(collection_name, parsed_data)

    def fetch_and_save_postgres(self, table_name):
        """
        Fetch data from a PostgreSQL table and save to JSON.
        """
        data = self.pg_conn.fetch_all(table_name)
        if data:
            self.json_manager.write_json(table_name, data)