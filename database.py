import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "campus_lost_found.db")


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a database connection with dict-like row access."""
    path = db_path if db_path is not None else DEFAULT_DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes the database schema if tables do not already exist."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('lost', 'found')),
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            color TEXT NOT NULL,
            description TEXT NOT NULL,
            date_reported TEXT NOT NULL,
            location TEXT NOT NULL,
            contact_info TEXT,
            status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Returned')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def create_item(
    item_type: str,
    title: str,
    category: str,
    color: str,
    description: str,
    date_reported: str,
    location: str,
    contact_info: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Inserts a new lost or found item record and returns its generated id."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO items (type, title, category, color, description, date_reported, location, contact_info, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active')
        """,
        (
            item_type.strip().lower(),
            title.strip(),
            category.strip(),
            color.strip(),
            description.strip(),
            date_reported.strip(),
            location.strip(),
            (contact_info or "").strip(),
        ),
    )
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id


def get_item_by_id(item_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieves an item by its id."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_items(
    item_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    search_query: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves items based on optional filters."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if item_type:
        query += " AND type = ?"
        params.append(item_type.strip().lower())

    if status:
        query += " AND status = ?"
        params.append(status.strip())

    if category and category.lower() != "all":
        query += " AND category = ?"
        params.append(category.strip())

    if search_query:
        query += " AND (title LIKE ? OR description LIKE ? OR location LIKE ? OR color LIKE ?)"
        wildcard = f"%{search_query.strip()}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_item_status(item_id: int, new_status: str, db_path: Optional[str] = None) -> bool:
    """Updates the status of an item (e.g. 'Returned' or 'Active')."""
    if new_status not in ("Active", "Returned"):
        raise ValueError(f"Invalid status: {new_status}")

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE items SET status = ? WHERE id = ?",
        (new_status, item_id),
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def delete_item(item_id: int, db_path: Optional[str] = None) -> bool:
    """Deletes an item record by id."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0


def get_dashboard_stats(db_path: Optional[str] = None) -> Dict[str, int]:
    """Computes high-level counts for the dashboard."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM items WHERE type = 'lost'")
    total_lost = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE type = 'found'")
    total_found = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE status = 'Returned'")
    total_returned = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM items WHERE status = 'Active'")
    total_active = cursor.fetchone()[0]

    conn.close()
    return {
        "total_lost": total_lost,
        "total_found": total_found,
        "total_returned": total_returned,
        "total_active": total_active,
    }
