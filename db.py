import sqlite3
from math import radians, sin, cos, sqrt, atan2

DB_NAME = "food_waste.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        latitude REAL,
        longitude REAL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ngos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        latitude REAL,
        longitude REAL,
        capacity INTEGER
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS surplus_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER,
        item_name TEXT,
        quantity INTEGER,
        expiry_minutes INTEGER,
        status TEXT DEFAULT 'available',
        matched_ngo TEXT
    )""")

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM restaurants")
    if cursor.fetchone()[0] == 0:
        restaurants = [
            ("Bismillah Bakery", 24.8607, 67.0011),
            ("Al-Karam Restaurant", 24.8650, 67.0100),
            ("City Hotel", 24.8500, 67.0200),
        ]
        cursor.executemany("INSERT INTO restaurants (name, latitude, longitude) VALUES (?, ?, ?)", restaurants)

        ngos = [
            ("Umeed Foundation", 24.8620, 67.0050, 50),
            ("Sailani Welfare", 24.8580, 67.0150, 100),
            ("Student Hostel Trust", 24.8700, 67.0080, 30),
        ]
        cursor.executemany("INSERT INTO ngos (name, latitude, longitude, capacity) VALUES (?, ?, ?, ?)", ngos)
        conn.commit()

    conn.close()


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def calculate_match_score(distance_km, expiry_minutes, quantity, ngo_capacity):
    distance_score = distance_km * 10
    urgency_penalty = expiry_minutes * 0.5
    capacity_penalty = 1000 if quantity > ngo_capacity else 0
    return round(distance_score + urgency_penalty + capacity_penalty, 2)


def find_best_matches(restaurant_lat, restaurant_lon, expiry_minutes, quantity, top_n=3):
    conn = get_connection()
    ngos = conn.execute("SELECT * FROM ngos").fetchall()
    conn.close()

    results = []
    for ngo in ngos:
        distance = calculate_distance(restaurant_lat, restaurant_lon, ngo["latitude"], ngo["longitude"])
        score = calculate_match_score(distance, expiry_minutes, quantity, ngo["capacity"])
        results.append({
            "ngo_id": ngo["id"],
            "ngo_name": ngo["name"],
            "distance_km": round(distance, 2),
            "score": score
        })
    results.sort(key=lambda x: x["score"])
    return results[:top_n]


def get_restaurants():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM restaurants").fetchall()
    conn.close()
    return rows


def post_surplus(restaurant_id, item_name, quantity, expiry_minutes):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO surplus_posts (restaurant_id, item_name, quantity, expiry_minutes) VALUES (?, ?, ?, ?)",
        (restaurant_id, item_name, quantity, expiry_minutes)
    )
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id


def confirm_pickup(post_id, ngo_name):
    conn = get_connection()
    conn.execute(
        "UPDATE surplus_posts SET status = 'picked_up', matched_ngo = ? WHERE id = ?",
        (ngo_name, post_id)
    )
    conn.commit()
    conn.close()


def get_impact_stats():
    """Returns total meals saved and total pickups completed - for the Impact dashboard"""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as pickups, COALESCE(SUM(quantity), 0) as total_qty "
        "FROM surplus_posts WHERE status = 'picked_up'"
    ).fetchone()
    conn.close()
    total_pickups = row["pickups"]
    total_qty = row["total_qty"]
    # Rough estimate: 1 unit of surplus item ≈ 1 meal
    people_helped = total_qty
    return {
        "pickups": total_pickups,
        "meals_saved": total_qty,
        "people_helped": people_helped
    }
