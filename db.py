"""
db.py — Database layer para sa Karinderya Management System (SQLite + pandas).
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "karinderya.db")

DEFAULT_MENU = [
    ("Adobo", 60),
    ("Sinigang", 70),
    ("Kare-Kare", 90),
    ("Pinakbet", 55),
    ("Tinola", 60),
    ("Menudo", 65),
    ("Dinuguan", 65),
    ("Lechon Kawali", 85),
    ("Pritong Isda", 70),
    ("Kanin", 15),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Gumawa ng tables kung wala pa."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            dish_name   TEXT    UNIQUE NOT NULL,
            price       REAL    NOT NULL,
            is_active   INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date   TEXT    NOT NULL,
            sale_time   TEXT    NOT NULL,
            dish_name   TEXT    NOT NULL,
            quantity    INTEGER NOT NULL,
            price       REAL    NOT NULL,
            total       REAL    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        )
    """)

    # Insert default menu kung walang laman
    cur.execute("SELECT COUNT(*) FROM menu")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO menu (dish_name, price) VALUES (?, ?)",
            DEFAULT_MENU,
        )

    conn.commit()
    conn.close()


# ── Menu CRUD ────────────────────────────────────────────────────────────────

def get_menu() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, dish_name, price, is_active FROM menu ORDER BY dish_name", conn
    )
    conn.close()
    return df


def get_active_dishes() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, dish_name, price FROM menu WHERE is_active=1 ORDER BY dish_name",
        conn,
    )
    conn.close()
    return df


def add_dish(dish_name: str, price: float):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO menu (dish_name, price) VALUES (?, ?)",
            (dish_name.strip(), price),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Kung existing na pero inactive, i-reactivate
        conn.execute(
            "UPDATE menu SET is_active=1, price=? WHERE dish_name=?",
            (price, dish_name.strip()),
        )
        conn.commit()
    finally:
        conn.close()


def update_dish(dish_id: int, dish_name: str, price: float):
    conn = get_connection()
    conn.execute(
        "UPDATE menu SET dish_name=?, price=? WHERE id=?",
        (dish_name.strip(), price, dish_id),
    )
    conn.commit()
    conn.close()


def delete_dish(dish_id: int):
    conn = get_connection()
    conn.execute("UPDATE menu SET is_active=0 WHERE id=?", (dish_id,))
    conn.commit()
    conn.close()


# ── Sales CRUD ───────────────────────────────────────────────────────────────

def add_sale(sale_date: str, sale_time: str, dish_name: str, quantity: int, price: float):
    total = quantity * price
    conn = get_connection()
    conn.execute(
        """INSERT INTO sales (sale_date, sale_time, dish_name, quantity, price, total)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (sale_date, sale_time, dish_name, quantity, price, total),
    )
    conn.commit()
    conn.close()


def update_sale(sale_id: int, sale_date: str, sale_time: str, dish_name: str, quantity: int, price: float):
    total = quantity * price
    conn = get_connection()
    conn.execute(
        """UPDATE sales
           SET sale_date=?, sale_time=?, dish_name=?, quantity=?, price=?, total=?
           WHERE id=?""",
        (sale_date, sale_time, dish_name, quantity, price, total, sale_id),
    )
    conn.commit()
    conn.close()


def delete_sale(sale_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM sales WHERE id=?", (sale_id,))
    conn.commit()
    conn.close()


def get_all_sales() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM sales ORDER BY sale_date DESC, sale_time DESC", conn
    )
    conn.close()
    return df


def get_sales_range(start_date: str, end_date: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM sales WHERE sale_date BETWEEN ? AND ? ORDER BY sale_date, sale_time",
        conn,
        params=(start_date, end_date),
    )
    conn.close()
    return df


# ── Aggregation helpers ──────────────────────────────────────────────────────

def sales_summary(df: pd.DataFrame) -> dict:
    """Buuin ang summary dict mula sa sales DataFrame para sa AI / dashboard."""
    if df.empty:
        return {
            "total_sales": 0,
            "total_transactions": 0,
            "avg_daily_sales": 0,
            "top_dishes": [],
            "bottom_dishes": [],
            "daily_sales": [],
            "hourly_sales": [],
            "dish_breakdown": [],
        }

    df = df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["hour"] = df["sale_time"].apply(lambda t: int(t.split(":")[0]))
    df["day_name"] = df["sale_date"].dt.day_name()

    total_sales = float(df["total"].sum())
    num_days = max((df["sale_date"].max() - df["sale_date"].min()).days, 1)

    by_dish = (
        df.groupby("dish_name")
        .agg(qty=("quantity", "sum"), revenue=("total", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index()
    )

    daily = (
        df.groupby(df["sale_date"].dt.strftime("%Y-%m-%d"))
        .agg(revenue=("total", "sum"))
        .reset_index()
    )
    daily.columns = ["date", "revenue"]

    hourly = (
        df.groupby("hour")
        .agg(revenue=("total", "sum"), qty=("quantity", "sum"))
        .reset_index()
    )

    by_day_name = (
        df.groupby("day_name")
        .agg(avg_revenue=("total", "mean"), qty=("quantity", "sum"))
        .reset_index()
    )

    return {
        "total_sales": total_sales,
        "total_transactions": len(df),
        "avg_daily_sales": round(total_sales / num_days, 2),
        "top_dishes": by_dish.head(5).to_dict("records"),
        "bottom_dishes": by_dish.tail(3).to_dict("records"),
        "daily_sales": daily.to_dict("records"),
        "hourly_sales": hourly.to_dict("records"),
        "dish_breakdown": by_dish.to_dict("records"),
        "by_day_name": by_day_name.to_dict("records"),
    }


# ── Sample-data generator ───────────────────────────────────────────────────

def generate_sample_data(days: int = 60):
    """I-generate ang random sales data para sa testing."""
    conn = get_connection()
    conn.execute("DELETE FROM sales")  # clear muna

    menu = get_active_dishes()
    if menu.empty:
        conn.close()
        return

    dishes = list(zip(menu["dish_name"], menu["price"]))
    today = datetime.now().date()

    rows = []
    for d in range(days):
        date = today - timedelta(days=days - 1 - d)
        # Mas maraming benta sa weekends
        is_weekend = date.weekday() >= 5
        num_sales = random.randint(15, 35) if is_weekend else random.randint(8, 25)

        for _ in range(num_sales):
            dish_name, price = random.choice(dishes)
            # Mas popular ang Adobo, Sinigang, Kanin
            if dish_name in ("Adobo", "Sinigang", "Kanin"):
                if random.random() < 0.3:
                    dish_name, price = random.choice(dishes)

            # Realistic hours: 6AM-2PM lunch, 5PM-8PM dinner
            if random.random() < 0.65:
                hour = random.randint(6, 13)  # lunch rush
            else:
                hour = random.randint(17, 20)  # dinner

            minute = random.randint(0, 59)
            qty = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
            sale_time = f"{hour:02d}:{minute:02d}"
            total = qty * price

            rows.append((
                date.isoformat(),
                sale_time,
                dish_name,
                qty,
                price,
                total,
            ))

    conn.executemany(
        """INSERT INTO sales (sale_date, sale_time, dish_name, quantity, price, total)
           VALUES (?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)
