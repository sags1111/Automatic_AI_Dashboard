import json
import sqlite3
import pandas as pd
import os

# ── Connect to database ───────────────────────────────────────────────────────
def connect_db(db_path="Chinook_Sqlite.sqlite"):
    if not os.path.exists(db_path):
        print(f"ERROR: Database file '{db_path}' not found!")
        exit(1)
    return sqlite3.connect(db_path)

# ── Load schema ───────────────────────────────────────────────────────────────
def load_schema(schema_path="schema/schema.json"):
    with open(schema_path, "r") as f:
        return json.load(f)

# ── Analyze each table ────────────────────────────────────────────────────────
def analyze_table(conn, table_name: str) -> dict:
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        return {"error": str(e)}

    result = {}

    # Basic stats
    result["total_rows"] = len(df)
    result["total_columns"] = len(df.columns)
    result["columns"] = list(df.columns)

    # Missing values
    missing = df.isnull().sum()
    result["missing_values"] = {
        col: int(missing[col])
        for col in df.columns
        if missing[col] > 0
    }

    # Numeric column stats
    numeric_cols = df.select_dtypes(include=["number"]).columns
    result["numeric_stats"] = {}
    for col in numeric_cols:
        result["numeric_stats"][col] = {
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
            "avg": round(float(df[col].mean()), 2)
        }

    # Top 5 rows as sample
    result["sample_data"] = df.head(5).to_dict(orient="records")

    return result

# ── Run analysis on all tables ────────────────────────────────────────────────
def analyze_all_tables(conn, schema: dict) -> dict:
    all_results = {}
    tables = list(schema.keys())

    print(f"Analyzing {len(tables)} tables...")
    for i, table in enumerate(tables, 1):
        print(f"   [{i}/{len(tables)}] Analyzing {table}...")
        all_results[table] = analyze_table(conn, table)

    return all_results

# ── Save results ──────────────────────────────────────────────────────────────
def save_analysis(analysis: dict, output_path="schema/data_analysis.json"):
    with open(output_path, "w") as f:
        json.dump(analysis, f, indent=4, default=str)
    print(f"\nSaved to {output_path}")

# ── Print summary ─────────────────────────────────────────────────────────────
def print_summary(analysis: dict):
    print("\n" + "="*50)
    print("DATA ANALYSIS SUMMARY")
    print("="*50)

    total_rows = sum(t.get("total_rows", 0) for t in analysis.values())
    print(f"\nTotal Tables  : {len(analysis)}")
    print(f"Total Rows    : {total_rows:,}")

    print(f"\nTable Overview:")
    for table, data in analysis.items():
        rows = data.get("total_rows", 0)
        cols = data.get("total_columns", 0)
        missing = len(data.get("missing_values", {}))
        print(f"   - {table}: {rows} rows, {cols} columns, {missing} columns with missing values")

    print("\n" + "="*50)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Step 3: Data Analysis with Pandas")
    print("Connecting to database...")

    conn = connect_db()
    print("Connected!")

    schema = load_schema()
    analysis = analyze_all_tables(conn, schema)

    print_summary(analysis)
    save_analysis(analysis)

    conn.close()
    print("Done!")