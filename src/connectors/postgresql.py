import psycopg2
import psycopg2.extras

class PostgreSQLConnector:
    """A connector class for interacting with a PostgreSQL database."""

    def __init__(self, host, port, database, user, password):
        """Initializes the PostgreSQLConnector.

        Args:
            host (str): The database server host.
            port (int): The database server port.
            database (str): The name of the database.
            user (str): The username for authentication.
            password (str): The password for authentication.

        Raises:
            Exception: If the connection to the database fails.
        """
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
        """Fetches all rows from a PostgreSQL table.

        Args:
            table_name (str): The name of the table to fetch from.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary
                        represents a row. Returns an empty list if an
                        error occurs.
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(f"SELECT * FROM {table_name}")
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching data from PostgreSQL table {table_name}: {e}")
            return []

    def close(self):
        """Closes the PostgreSQL connection."""
        if self.conn:
            self.conn.close()