import psycopg2

class PostgreSQLConnector:
    def __init__(self, host, port, database, user, password):
        try:
            self.conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            raise

    def fetch_all(self, table_name):
        """
        Fetch all rows from a PostgreSQL table.
        Returns a list of dictionaries, where each dictionary represents a row.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {table_name}")
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error fetching data from PostgreSQL table {table_name}: {e}")
            return []

    def close(self):
        """Close the PostgreSQL connection."""
        if self.conn:
            self.conn.close()