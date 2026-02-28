"""
Simple SQLite storage for blocks (block hash, prev hash, height, timestamp, raw JSON).
"""
import json
import sqlite3
import os


def get_db_path(node_id: str) -> str:
    return f"blocks_{node_id}.db"


def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            block_hash TEXT PRIMARY KEY,
            prev_hash TEXT NOT NULL,
            height INTEGER NOT NULL,
            timestamp REAL NOT NULL,
            data TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_height ON blocks(height)")
    conn.commit()
    conn.close()


def insert_block(db_path: str, block: dict):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR IGNORE INTO blocks (block_hash, prev_hash, height, timestamp, data) VALUES (?,?,?,?,?)",
        (
            block["BlockHash"],
            block["PrevHash"],
            block["Height"],
            block["Timestamp"],
            json.dumps(block),
        ),
    )
    conn.commit()
    conn.close()


def get_block_by_hash(db_path: str, block_hash: str) -> dict | None:
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT data FROM blocks WHERE block_hash = ?", (block_hash,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def get_block_by_height(db_path: str, height: int) -> dict | None:
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT data FROM blocks WHERE height = ?", (height,)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def get_max_height(db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT MAX(height) FROM blocks").fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else -1


def block_hash_exists(db_path: str, block_hash: str) -> bool:
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT 1 FROM blocks WHERE block_hash = ?", (block_hash,)).fetchone()
    conn.close()
    return row is not None
