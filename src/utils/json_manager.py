import json
import os
from threading import Lock
from datetime import datetime, date
from bson import ObjectId

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

class JSONManager:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.lock = Lock()
        os.makedirs(data_dir, exist_ok=True)

    def write_json(self, filename, data):
        """
        Write data to a JSON file.
        """
        file_path = os.path.join(self.data_dir, f"{filename}.json")
        with self.lock:
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, cls=CustomJSONEncoder, indent=2)
            except Exception as e:
                print(f"Error writing to {file_path}: {e}")

    def update_json(self, filename, operation, record, id_field='id'):
        """
        Update a JSON file based on the operation (INSERT, UPDATE, DELETE).
        """
        file_path = os.path.join(self.data_dir, f"{filename}.json")
        with self.lock:
            try:
                # Load existing data
                data = []
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                
                if not isinstance(data, list):
                    data = [data] if data else []

                # Process operation
                record_id = record.get(id_field)
                if operation == 'INSERT':
                    data.append(record)
                elif operation == 'UPDATE':
                    for i, item in enumerate(data):
                        if item.get(id_field) == record_id:
                            data[i] = record
                            break
                    else:
                        data.append(record)
                elif operation == 'DELETE':
                    data = [item for item in data if item.get(id_field) != record_id]

                # Write updated data
                with open(file_path, 'w') as f:
                    json.dump(data, f, cls=CustomJSONEncoder, indent=2)
            except Exception as e:
                print(f"Error updating {file_path}: {e}")

    def load_json(self, filename):
        """
        Load data from a JSON file.
        """
        file_path = os.path.join(self.data_dir, f"{filename}.json")
        with self.lock:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        return json.load(f)
                return []
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                return []