import sqlite3
import secrets
import time
import os
from urllib.parse import urlparse

DB_PATH = os.environ.get("URL_SHORTENER_DB", "urls.db")

CREATE_TABLE_SQL = """CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    created_at REAL NOT NULL,
    visits INTEGER NOT NULL DEFAULT 0
);"""


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not urlparse(url).scheme:
        url = 'http://' + url
    return url


def generate_code(length: int = 6) -> str:
    # generate a short alphanumeric token; retry until unique
    while True:
        token = secrets.token_urlsafe(4)
        code = ''.join([c for c in token if c.isalnum()])[:length]
        if not code:
            continue
        if not get_url(code):
            return code


def add_url(url: str) -> str:
    url = _normalize_url(url)
    conn = get_conn()
    cur = conn.cursor()
    for _ in range(5):
        code = generate_code()
        try:
            cur.execute("INSERT INTO urls (code, url, created_at) VALUES (?, ?, ?)", (code, url, time.time()))
            conn.commit()
            conn.close()
            return code
        except sqlite3.IntegrityError:
            continue
    conn.close()
    raise RuntimeError("Failed to create unique code")


def get_url(code: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM urls WHERE code = ?", (code,)).fetchone()
    conn.close()
    return row["url"] if row else None


def increment_visits(code: str):
    conn = get_conn()
    conn.execute("UPDATE urls SET visits = visits + 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()
