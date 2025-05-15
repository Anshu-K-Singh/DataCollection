import yaml
import os
import asyncio
from connectors.mongodb import MongoDBConnector
from connectors.postgresql import PostgreSQLConnector
from utils.json_manager import JSONManager
from fetcher.data_fetcher import DataFetcher
from monitor.mongo_monitor import MongoMonitor
from monitor.pg_monitor import PGMonitor

async def main():
    # Resolve config.yaml path relative to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, '..', 'config', 'config.yaml')

    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}. Please ensure config.yaml exists in the config directory.")
        return

    # Initialize connectors and managers
    try:
        mongo_conn = MongoDBConnector(
            config['mongodb']['uri'],
            config['mongodb']['database']
        )
        pg_conn = PostgreSQLConnector(
            config['postgresql']['host'],
            config['postgresql']['port'],
            config['postgresql']['database'],
            config['postgresql']['user'],
            config['postgresql']['password']
        )
        json_manager = JSONManager(config['json_dir'])
        data_fetcher = DataFetcher(mongo_conn, pg_conn, json_manager)

        # Fetch initial data
        print("Fetching initial data...")
        for collection in config['mongodb']['collections']:
            print(f"Fetching data from MongoDB collection: {collection}")
            data_fetcher.fetch_and_save_mongo(collection)
        for table in config['postgresql']['tables']:
            print(f"Fetching data from PostgreSQL table: {table}")
            data_fetcher.fetch_and_save_postgres(table)

        # Combine and save data
        print("Combining data...")
        data_fetcher.combine_and_save_data()

        # Start change monitoring
        print("Starting change monitoring...")
        mongo_monitor = MongoMonitor(mongo_conn, json_manager, config['mongodb']['collections'], data_fetcher)
        pg_monitor = PGMonitor(pg_conn, json_manager, config['postgresql']['tables'], config, data_fetcher)

        # Run monitors concurrently
        await asyncio.gather(
            mongo_monitor.monitor_changes(),
            pg_monitor.monitor_changes()
        )

    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        mongo_conn.close()
        pg_conn.close()

if __name__ == '__main__':
    asyncio.run(main())