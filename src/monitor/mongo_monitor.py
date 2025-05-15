import asyncio
from bson import json_util
from utils.eda import clean_mongo_data

class MongoMonitor:
    def __init__(self, mongo_conn, json_manager, collections, data_fetcher):
        self.mongo_conn = mongo_conn
        self.json_manager = json_manager
        self.collections = collections
        self.data_fetcher = data_fetcher

    async def monitor_changes(self):
        """
        Monitor changes in MongoDB collections using Change Streams.
        Runs synchronous Change Stream iteration in a separate thread.
        """
        try:
            tasks = []
            for collection_name in self.collections:
                print(f"Starting Change Stream for MongoDB collection: {collection_name}")
                task = asyncio.create_task(self.monitor_collection(collection_name))
                tasks.append(task)
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"Error in MongoDB Change Stream monitoring: {e}")

    async def monitor_collection(self, collection_name):
        """
        Monitor a single MongoDB collection in a threaded context.
        """
        try:
            await asyncio.to_thread(self.process_collection_changes, collection_name)
        except Exception as e:
            print(f"Error monitoring collection {collection_name}: {e}")

    def process_collection_changes(self, collection_name):
        """
        Process changes for a MongoDB collection using a synchronous Change Stream.
        """
        change_stream = self.mongo_conn.get_change_stream(collection_name)
        try:
            for change in change_stream:
                operation = change['operationType']
                if operation in ['insert', 'update', 'delete']:
                    self.process_change(collection_name, operation, change)
        finally:
            change_stream.close()

    def process_change(self, collection_name, operation, change):
        """
        Process a change event and update the corresponding JSON file.
        """
        try:
            if operation == 'insert':
                document = change['fullDocument']
                if document:
                    cleaned_document = clean_mongo_data(document)
                    self.json_manager.update_json(collection_name, 'INSERT', cleaned_document, id_field='_id')
                    if collection_name == "projects":
                        self.data_fetcher.update_combined_data_for_project(cleaned_document, 'INSERT')
            elif operation == 'update':
                document = change['fullDocument']
                if document:
                    cleaned_document = clean_mongo_data(document)
                    self.json_manager.update_json(collection_name, 'UPDATE', cleaned_document, id_field='_id')
                    if collection_name == "projects":
                        self.data_fetcher.update_combined_data_for_project(cleaned_document, 'UPDATE')
            elif operation == 'delete':
                document_id = change['documentKey']['_id']
                self.json_manager.update_json(collection_name, 'DELETE', {'_id': document_id}, id_field='_id')
                if collection_name == "projects":
                    self.data_fetcher.update_combined_data_for_project({'_id': document_id}, 'DELETE')
        except Exception as e:
            print(f"Error processing change for {collection_name}: {e}")