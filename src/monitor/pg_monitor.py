import select
import psycopg2
import asyncio
from psycopg2 import OperationalError

class PGMonitor:
    def __init__(self, pg_conn, json_manager, tables, config):
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
        """
        Monitor PostgreSQL tables using LISTEN/NOTIFY with reconnection logic.
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

    def process_change(self, table_name, operation, record_id):
        """
        Process a change event from the change_log table and update the JSON file.
        """
        try:
            # Use the existing connection for querying change_log
            with self.pg_conn.conn.cursor() as cur:
                cur.execute(
                    "SELECT operation, new_data FROM change_log WHERE table_name = %s AND record_id = %s ORDER BY timestamp DESC LIMIT 1",
                    (table_name, record_id)
                )
                result = cur.fetchone()
                if result:
                    op, new_data = result
                    if op == 'INSERT' or op == 'UPDATE':
                        if new_data:
                            self.json_manager.update_json(table_name, op, new_data, id_field='id')
                    elif op == 'DELETE':
                        self.json_manager.update_json(table_name, 'DELETE', {'id': record_id}, id_field='id')
        except Exception as e:
            print(f"Error processing change for {table_name}: {e}")