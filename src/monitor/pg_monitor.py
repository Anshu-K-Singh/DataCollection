import select
import psycopg2
import asyncio
from psycopg2 import OperationalError
from src.connectors.postgresql import PostgreSQLConnector
from src.utils.json_manager import JSONManager

class PGMonitor:
    """A class to monitor real-time changes in PostgreSQL tables."""

    def __init__(self, pg_conn: PostgreSQLConnector, json_manager: JSONManager, tables: list[str], config: dict):
        """Initializes the PGMonitor.

        Args:
            pg_conn (PostgreSQLConnector): An instance of PostgreSQLConnector.
            json_manager (JSONManager): An instance of JSONManager.
            tables (list[str]): A list of table names to monitor.
            config (dict): The application configuration.
        """
        self.pg_conn = pg_conn
        self.json_manager = json_manager
        self.tables = tables
        self.conn_params = {
            'host': self.pg_conn.conn.get_dsn_parameters()['host'],
            'port': self.pg_conn.conn.get_dsn_parameters()['port'],
            'database': self.pg_conn.conn.get_dsn_parameters()['dbname'],
            'user': self.pg_conn.conn.get_dsn_parameters()['user'],
            'password': config['postgresql']['password'],
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }

    async def monitor_changes(self):
        """Monitors PostgreSQL tables using LISTEN/NOTIFY with reconnection logic.

        This method listens for notifications on the 'table_change' channel.
        It includes a reconnection loop to handle connection drops.
        """
        while True:
            conn = None
            try:
                # Create a new connection for listening
                conn = psycopg2.connect(**self.conn_params)
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                cursor = conn.cursor()
                cursor.execute("LISTEN table_change;")
                print("Listening for PostgreSQL table changes...")

                while True:
                    if select.select([conn], [], [], 5) == ([], [], []):
                        continue
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        table_name, operation, record_id = notify.payload.split(':')
                        if table_name in self.tables:
                            self.process_change(table_name, operation, int(record_id))
            except OperationalError as e:
                print(f"PostgreSQL connection error: {e}. Reconnecting in 5 seconds...")
                if conn:
                    conn.close()
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error in PostgreSQL change monitoring: {e}. Reconnecting in 5 seconds...")
                if conn:
                    conn.close()
                await asyncio.sleep(5)
            finally:
                if conn and not conn.closed:
                    conn.close()

    def process_change(self, table_name: str, operation: str, record_id: int):
        """Processes a change event from the change_log table and updates the JSON file.

        Args:
            table_name (str): The name of the table that was changed.
            operation (str): The operation type (e.g., 'INSERT', 'UPDATE', 'DELETE').
            record_id (int): The ID of the changed record.
        """
        try:
            with self.pg_conn.conn.cursor() as cur:
                cur.execute(
                    "SELECT operation, new_data FROM change_log WHERE table_name = %s AND record_id = %s ORDER BY timestamp DESC LIMIT 1",
                    (table_name, record_id)
                )
                result = cur.fetchone()
                if result:
                    op, new_data = result
                    if op in ['INSERT', 'UPDATE']:
                        if new_data:
                            self.json_manager.update_json(table_name, op, new_data, id_field='id')
                    elif op == 'DELETE':
                        self.json_manager.update_json(table_name, 'DELETE', {'id': record_id}, id_field='id')
        except Exception as e:
            print(f"Error processing change for {table_name}: {e}")