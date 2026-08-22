import sqlite3

from adapters.base_adapter import BaseAdapter


class SQLiteAdapter(BaseAdapter):

    def __init__(self, database_path):
        self.database_path = database_path
        self.connection = None

    def connect(self):
        """
        Establish a connection to the SQLite database.
        """
        self.connection = sqlite3.connect(self.database_path)
        print(f"Connected to {self.database_path}")

    def extract_schema(self):
        """
        Extract database schema.
        """

        cursor = self.connection.cursor()

        schema = {}

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name NOT LIKE 'sqlite_%';
        """)

        tables = cursor.fetchall()

        for table in tables:

            table_name = table[0]

            cursor.execute(f"PRAGMA table_info({table_name});")

            columns = cursor.fetchall()

            schema[table_name] = {
                "columns": []
            }

            for column in columns:

                column_info = {
                    "name": column[1],
                    "type": column[2],
                    "nullable": not bool(column[3]),
                    "primary_key": bool(column[5])
                }

                schema[table_name]["columns"].append(column_info)

        return schema

    def disconnect(self):
        """
        Close the database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Database connection closed.")