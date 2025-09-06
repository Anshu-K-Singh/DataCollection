import asyncio
from src.connectors.mongodb import MongoDBConnector
from src.utils.json_manager import JSONManager

class MongoMonitor:
    """A class to monitor real-time changes in MongoDB collections."""

    def __init__(self, mongo_conn: MongoDBConnector, json_manager: JSONManager, collections: list[str]):
        """Initializes the MongoMonitor.

        Args:
            mongo_conn (MongoDBConnector): An instance of MongoDBConnector.
            json_manager (JSONManager): An instance of JSONManager.
            collections (list[str]): A list of collection names to monitor.
        """
        self.mongo_conn = mongo_conn
        self.json_manager = json_manager
        self.collections = collections

    async def monitor_changes(self):
        """Monitors changes in MongoDB collections using Change Streams.

        This async method creates and runs a monitoring task for each specified
        collection concurrently.
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

    async def monitor_collection(self, collection_name: str):
        """Monitors a single MongoDB collection in a separate thread.

        This is a helper for `monitor_changes` that runs the synchronous
        change processing in a thread to avoid blocking the asyncio event loop.

        Args:
            collection_name (str): The name of the collection to monitor.
        """
        try:
            await asyncio.to_thread(self.process_collection_changes, collection_name)
        except Exception as e:
            print(f"Error monitoring collection {collection_name}: {e}")

    def process_collection_changes(self, collection_name: str):
        """Processes changes for a MongoDB collection using a synchronous Change Stream.

        This method opens a Change Stream on a collection and listens for
        insert, update, and delete operations, processing each change as it arrives.

        Args:
            collection_name (str): The name of the collection to process changes for.
        """
        change_stream = self.mongo_conn.get_change_stream(collection_name)
        try:
            for change in change_stream:
                operation = change['operationType']
                if operation in ['insert', 'update', 'delete']:
                    self.process_change(collection_name, operation, change)
        finally:
            change_stream.close()

    def process_change(self, collection_name: str, operation: str, change: dict):
        """Processes a single change event and updates the corresponding JSON file.

        Args:
            collection_name (str): The name of the collection where the change occurred.
            operation (str): The type of operation ('insert', 'update', 'delete').
            change (dict): The change event document from the Change Stream.
        """
        try:
            if operation == 'insert':
                document = change['fullDocument']
                self.json_manager.update_json(collection_name, 'INSERT', document, id_field='_id')
            elif operation == 'update':
                document = change['fullDocument']
                if document:  # fullDocument may be None if not available
                    self.json_manager.update_json(collection_name, 'UPDATE', document, id_field='_id')
            elif operation == 'delete':
                document_id = change['documentKey']['_id']
                self.json_manager.update_json(collection_name, 'DELETE', {'_id': document_id}, id_field='_id')
        except Exception as e:
            print(f"Error processing change for {collection_name}: {e}")