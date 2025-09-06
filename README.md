# Real-Time Data Synchronization and Monitoring

This project provides a real-time data synchronization and monitoring solution for MongoDB and PostgreSQL databases. It fetches initial data from both databases, saves it to JSON files, and then monitors for any subsequent changes (inserts, updates, deletes) in real-time, keeping the JSON files up-to-date.

## Purpose

The primary goal of this project is to maintain a synchronized copy of data from different database systems in a unified format (JSON). This can be useful for various purposes, such as:

-   **Data Warehousing**: Aggregating data from multiple sources.
-   **Auditing**: Keeping a log of all data modifications.
-   **Caching**: Providing a fast-access cache of database records.
-   **Microservices**: Enabling communication and data sharing between services that use different database technologies.

## Features

-   **Dual Database Support**: Connects to both MongoDB and PostgreSQL.
-   **Initial Data Fetch**: Performs an initial full data dump from specified collections and tables.
-   **Real-Time Monitoring**:
    -   Uses **Change Streams** for MongoDB to capture changes instantly.
    -   Uses **LISTEN/NOTIFY** with database triggers for PostgreSQL to get immediate notifications.
-   **JSON Storage**: Stores and updates data in local JSON files, organized by table or collection name.
-   **Asynchronous Operations**: Built with `asyncio` to handle concurrent monitoring of multiple data sources efficiently.
-   **Resilient Connections**: Includes automatic reconnection logic for the PostgreSQL monitor.

## Project Structure

```
.
├── config/
│   └── config.yaml           # Configuration file for database connections and settings.
├── src/
│   ├── connectors/
│   │   ├── mongodb.py        # MongoDB connection handler.
│   │   └── postgresql.py     # PostgreSQL connection handler.
│   ├── data/                 # Default directory for JSON data files.
│   ├── fetcher/
│   │   └── data_fetcher.py   # Fetches initial data from databases.
│   ├── monitor/
│   │   ├── mongo_monitor.py  # Monitors MongoDB collections for changes.
│   │   └── pg_monitor.py     # Monitors PostgreSQL tables for changes.
│   ├── scripts/
│   │   └── setup_pg_triggers.sql # SQL script to set up PostgreSQL triggers.
│   ├── utils/
│   │   └── json_manager.py   # Manages reading and writing of JSON files.
│   └── main.py               # Main entry point of the application.
└── README.md
```

## Setup

### Prerequisites

-   Python 3.7+
-   MongoDB Server
-   PostgreSQL Server
-   `pip` for installing Python packages.

### Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Python dependencies:**

    It's recommended to use a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

    Install the required packages from `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```
    *(Note: A `requirements.txt` file would need to be created for this step. See the "Creating `requirements.txt`" section below.)*

### Configuration

1.  **Rename `config/config.yaml.example` to `config/config.yaml`** (if an example file is provided) or create a new `config.yaml` file inside the `config` directory.

2.  **Update `config/config.yaml`** with your database credentials and settings:

    ```yaml
    mongodb:
      uri: "mongodb://localhost:27017/"
      database: "your_mongo_db"
      collections:
        - "users"
        - "products"

    postgresql:
      host: "localhost"
      port: 5432
      database: "your_pg_db"
      user: "your_pg_user"
      password: "your_pg_password"
      tables:
        - "orders"
        - "customers"

    json_dir: "src/data"
    ```

### PostgreSQL Trigger Setup

To enable real-time monitoring for PostgreSQL, you need to set up a trigger and a function in your database.

1.  **Connect to your PostgreSQL database** using `psql` or any other client.

2.  **Execute the SQL script** provided in `src/scripts/setup_pg_triggers.sql`. This script will:
    -   Create a `change_log` table to record all modifications.
    -   Create a function that logs changes to the `change_log` table and sends a notification.
    -   Create triggers on the tables you want to monitor (e.g., `orders`, `customers`). You will need to add a `CREATE TRIGGER` statement for each table specified in your `config.yaml`.

    Example of executing the script:
    ```bash
    psql -h localhost -U your_pg_user -d your_pg_db -f src/scripts/setup_pg_triggers.sql
    ```

## Usage

To run the application, simply execute the `main.py` script:

```bash
python src/main.py
```

The application will perform the following steps:
1.  Fetch all data from the specified MongoDB collections and PostgreSQL tables.
2.  Save the fetched data into JSON files in the directory specified by `json_dir` in the config.
3.  Start monitoring both databases for any changes and update the corresponding JSON files in real-time.

## Creating `requirements.txt`

To ensure all dependencies are managed, you can create a `requirements.txt` file with the following content. These are the likely dependencies for this project.

```
pyyaml
pymongo
psycopg2-binary
```

Then, you can install them using:
```bash
pip install -r requirements.txt
```
