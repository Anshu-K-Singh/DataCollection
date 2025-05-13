import json
import os
from datetime import datetime, date
from bson import ObjectId
import decimal

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle ObjectId, datetime, date, and Decimal."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, (datetime, date)):  # handle both datetime and date
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)

class JSONManager:
    def __init__(self, json_dir):
        self.json_dir = json_dir
        os.makedirs(json_dir, exist_ok=True)

    def write_json(self, filename, data):
        """
        Write data to a JSON file using custom encoder.
        """
        try:
            filepath = os.path.join(self.json_dir, f"{filename}.json")
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
            print(f"Data written to {filepath}")
        except Exception as e:
            print(f"Error writing to JSON file {filename}: {e}")

    def read_json(self, filename):
        """
        Read data from a JSON file.
        Returns empty list if file doesn't exist.
        """
        filepath = os.path.join(self.json_dir, f"{filename}.json")
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Error reading JSON file {filename}: {e}")
            return []

    def update_json(self, filename, operation, record, id_field='id'):
        """
        Update JSON file based on operation (INSERT, UPDATE, DELETE).
        id_field: '_id' for MongoDB, 'id' for PostgreSQL.
        """
        data = self.read_json(filename)
        record_id = record.get(id_field)

        if operation == 'INSERT':
            data.append(record)
        elif operation == 'UPDATE':
            for i, item in enumerate(data):
                if item.get(id_field) == record_id:
                    data[i] = record
                    break
        elif operation == 'DELETE':
            data = [item for item in data if item.get(id_field) != record_id]
        else:
            print(f"Unknown operation: {operation}")
            return

        self.write_json(filename, data)
        print(f"Updated {filename}.json with {operation} for record {record_id}")