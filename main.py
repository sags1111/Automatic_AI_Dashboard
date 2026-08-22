from adapters.sqlite_adapter import SQLiteAdapter
from schema.json_converter import JSONConverter


def main():
    print("Main function started")

    database_path = "Chinook_Sqlite.sqlite"

    output_file = "schema/schema.json"

    adapter = SQLiteAdapter(database_path)

    adapter.connect()

    schema = adapter.extract_schema()

    JSONConverter.save(schema, output_file)

    adapter.disconnect()


if __name__ == "__main__":
    main()

