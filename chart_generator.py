import json
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os


def connect_db(db_path="Chinook_Sqlite.sqlite"):
    if not os.path.exists(db_path):
        print(f"ERROR: Database file '{db_path}' not found!")
        exit(1)
    return sqlite3.connect(db_path)

# ── Load files ────────────────────────────────────────────────────────────────
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

# ── Create output folder for charts ──────────────────────────────────────────
def create_charts_folder():
    if not os.path.exists("charts"):
        os.makedirs("charts")
        print("Created charts/ folder")

# ── Chart 1: Top 10 Artists by Album Count ───────────────────────────────────
def chart_top_artists(conn):
    df = pd.read_sql_query("""
        SELECT ar.Name as Artist, COUNT(al.AlbumId) as Albums
        FROM Artist ar
        JOIN Album al ON ar.ArtistId = al.ArtistId
        GROUP BY ar.Name
        ORDER BY Albums DESC
        LIMIT 10
    """, conn)

    fig = px.bar(
        df, x="Artist", y="Albums",
        title="Top 10 Artists by Number of Albums",
        color="Albums",
        color_continuous_scale="blues"
    )
    fig.update_layout(xaxis_tickangle=-35)
    fig.write_html("charts/top_artists.html")
    print("   ✓ charts/top_artists.html")

# ── Chart 2: Sales by Country ─────────────────────────────────────────────────
def chart_sales_by_country(conn):
    df = pd.read_sql_query("""
        SELECT c.Country, ROUND(SUM(i.Total), 2) as Revenue
        FROM Customer c
        JOIN Invoice i ON c.CustomerId = i.CustomerId
        GROUP BY c.Country
        ORDER BY Revenue DESC
        LIMIT 10
    """, conn)

    fig = px.bar(
        df, x="Country", y="Revenue",
        title="Top 10 Countries by Revenue",
        color="Revenue",
        color_continuous_scale="greens"
    )
    fig.write_html("charts/sales_by_country.html")
    print("   ✓ charts/sales_by_country.html")


def chart_revenue_over_time(conn):
    df = pd.read_sql_query("""
        SELECT strftime('%Y-%m', InvoiceDate) as Month,
               ROUND(SUM(Total), 2) as Revenue
        FROM Invoice
        GROUP BY Month
        ORDER BY Month
    """, conn)

    fig = px.line(
        df, x="Month", y="Revenue",
        title="Monthly Revenue Over Time",
        markers=True
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.write_html("charts/revenue_over_time.html")
    print("   ✓ charts/revenue_over_time.html")

# ── Chart 4: Top 10 Genres by Track Count ────────────────────────────────────
def chart_genres(conn):
    df = pd.read_sql_query("""
        SELECT g.Name as Genre, COUNT(t.TrackId) as Tracks
        FROM Genre g
        JOIN Track t ON g.GenreId = t.GenreId
        GROUP BY g.Name
        ORDER BY Tracks DESC
        LIMIT 10
    """, conn)

    fig = px.pie(
        df, names="Genre", values="Tracks",
        title="Top 10 Genres by Track Count"
    )
    fig.write_html("charts/genres.html")
    print("   ✓ charts/genres.html")

# ── Chart 5: Top 10 Selling Tracks ───────────────────────────────────────────
def chart_top_tracks(conn):
    df = pd.read_sql_query("""
        SELECT t.Name as Track, ar.Name as Artist,
               COUNT(il.TrackId) as Sales
        FROM Track t
        JOIN InvoiceLine il ON t.TrackId = il.TrackId
        JOIN Album al ON t.AlbumId = al.AlbumId
        JOIN Artist ar ON al.ArtistId = ar.ArtistId
        GROUP BY t.TrackId
        ORDER BY Sales DESC
        LIMIT 10
    """, conn)

    fig = px.bar(
        df, x="Sales", y="Track",
        orientation="h",
        title="Top 10 Best Selling Tracks",
        color="Artist"
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.write_html("charts/top_tracks.html")
    print("   ✓ charts/top_tracks.html")

# ── Chart 6: Customer Growth Over Time ───────────────────────────────────────
def chart_customer_growth(conn):
    df = pd.read_sql_query("""
        SELECT strftime('%Y-%m', InvoiceDate) as Month,
               COUNT(DISTINCT CustomerId) as ActiveCustomers
        FROM Invoice
        GROUP BY Month
        ORDER BY Month
    """, conn)

    fig = px.line(
        df, x="Month", y="ActiveCustomers",
        title="Active Customers Per Month",
        markers=True,
        color_discrete_sequence=["orange"]
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.write_html("charts/customer_growth.html")
    print("   ✓ charts/customer_growth.html")

if __name__ == "__main__":
    print("Step 5: Automatic Chart Generator")
    print("Connecting to database...")

    conn = connect_db()
    create_charts_folder()

    print("\nGenerating charts...")
    chart_top_artists(conn)
    chart_sales_by_country(conn)
    chart_revenue_over_time(conn)
    chart_genres(conn)
    chart_top_tracks(conn)
    chart_customer_growth(conn)

    conn.close()

    print("\n" + "="*45)
    print("ALL CHARTS GENERATED!")
    print("="*45)
    print("\nOpen these files in your browser:")
    print("   - charts/top_artists.html")
    print("   - charts/sales_by_country.html")
    print("   - charts/revenue_over_time.html")
    print("   - charts/genres.html")
    print("   - charts/top_tracks.html")
    print("   - charts/customer_growth.html")
    print("\nNext Step: Run Step 6 to see all charts in one dashboard!")