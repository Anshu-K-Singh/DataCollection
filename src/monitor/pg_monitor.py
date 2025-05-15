import select
import psycopg2
import asyncio
from psycopg2 import OperationalError
from utils.eda import clean_postgres_data

class PGMonitor:
    def __init__(self, pg_conn, json_manager, tables, config, data_fetcher):
        self.pg_conn = pg_conn
        self.json_manager = json_manager
        self.tables = tables
        self.config = config
        self.data_fetcher = data_fetcher
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
                        try:
                            table_name, operation, record_id = notify.payload.split(':')
                            if table_name in self.tables:
                                self.process_change(table_name, operation, int(record_id))
                        except ValueError:
                            print(f"Invalid notification payload: {notify.payload}")
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
                            cleaned_data = clean_postgres_data(new_data, table_name)
                            self.json_manager.update_json(table_name, op, cleaned_data, id_field='id')
                            # Update cached data
                            if table_name == "job_interactions":
                                for i, ji in enumerate(self.data_fetcher.job_interactions):
                                    if ji.get("id") == cleaned_data.get("id"):
                                        self.data_fetcher.job_interactions[i] = cleaned_data
                                        break
                                else:
                                    self.data_fetcher.job_interactions.append(cleaned_data)
                                self.data_fetcher.update_combined_data_for_interaction(cleaned_data, op, record_id)
                            elif table_name == "job_actions":
                                for i, ja in enumerate(self.data_fetcher.job_actions):
                                    if ja.get("id") == cleaned_data.get("id"):
                                        self.data_fetcher.job_actions[i] = cleaned_data
                                        break
                                else:
                                    self.data_fetcher.job_actions.append(cleaned_data)
                                self.data_fetcher.update_combined_data_for_action(cleaned_data, op, record_id)
                    elif op == 'DELETE':
                        self.json_manager.update_json(table_name, 'DELETE', {'id': record_id}, id_field='id')
                        if table_name == "job_interactions":
                            self.data_fetcher.job_interactions = [ji for ji in self.data_fetcher.job_interactions if ji.get("id") != record_id]
                            self.data_fetcher.update_combined_data_for_interaction({}, op, record_id)
                        elif table_name == "job_actions":
                            self.data_fetcher.job_actions = [ja for ja in self.data_fetcher.job_actions if ja.get("id") != record_id]
                            self.data_fetcher.update_combined_data_for_action({}, op, record_id)
                else:
                    print(f"No change_log entry for {table_name} ID {record_id}")
        except Exception as e:
            print(f"Error processing change for {table_name}: {e}")