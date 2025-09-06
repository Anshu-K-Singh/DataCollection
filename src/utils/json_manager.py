import json
import os
from datetime import datetime, date
from bson import ObjectId
import decimal

class CustomJSONEncoder(json.JSONEncoder):
    """A custom JSON encoder to handle special data types.

    This encoder provides serialization for:
    - `ObjectId`: Converts to string.
    - `datetime` and `date`: Converts to ISO 8601 format string.
    - `Decimal`: Converts to float.
    """
    def default(self, obj):
        """Overrides the default JSONEncoder method.

        Args:
            obj: The object to encode.

        Returns:
            A serializable representation of the object.
        """
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)

class JSONManager:
    """A class to manage reading and writing JSON files."""

    def __init__(self, json_dir: str):
        """Initializes the JSONManager.

        Args:
            json_dir (str): The directory where JSON files will be stored.
        """
        self.json_dir = json_dir
        os.makedirs(json_dir, exist_ok=True)

    def write_json(self, filename: str, data: any):
        """Writes data to a JSON file using a custom encoder.

        Args:
            filename (str): The name of the file (without extension).
            data (any): The data to write to the file.
        """
        try:
            filepath = os.path.join(self.json_dir, f"{filename}.json")
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, cls=CustomJSONEncoder)
            print(f"Data written to {filepath}")
        except Exception as e:
            print(f"Error writing to JSON file {filename}: {e}")

    def read_json(self, filename: str) -> list | dict:
        """Reads data from a JSON file.

        Args:
            filename (str): The name of the file (without extension).

        Returns:
            list | dict: The data from the JSON file. Returns an empty list
                         if the file is not found or an error occurs.
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

    def update_json(self, filename: str, operation: str, record: dict, id_field: str = 'id'):
        """Updates a JSON file based on a specified operation.

        This method supports 'INSERT', 'UPDATE', and 'DELETE' operations.

        Args:
            filename (str): The name of the file (without extension).
            operation (str): The operation to perform ('INSERT', 'UPDATE', 'DELETE').
            record (dict): The record to be added, updated, or deleted.
            id_field (str): The name of the identifier field in the records.
                            Defaults to 'id'.
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