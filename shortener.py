import sqlite3
import secrets
import time
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.environ.get("URL_SHORTENER_DB", "urls.db")

# links can live for at most ten years
MAX_EXPIRY_SECONDS = 10 * 365 * 24 * 60 * 60

CREATE_TABLE_SQL = """CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    created_at REAL NOT NULL,
    visits INTEGER NOT NULL DEFAULT 0,
    expires_at REAL,
    password_hash TEXT
);"""


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute(CREATE_TABLE_SQL)
    # databases created before expiring/password protection existed have no column
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(urls)")}
    for column, coltype in (("expires_at", "REAL"), ("password_hash", "TEXT")):
        if column not in columns:
            conn.execute(f"ALTER TABLE urls ADD COLUMN {column} {coltype}")
    conn.commit()
    conn.close()


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not urlparse(url).scheme:
        url = 'http://' + url
    return url


def _code_exists(code: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM urls WHERE code = ?", (code,)).fetchone()
    conn.close()
    return row is not None


def generate_code(length: int = 6) -> str:
    while True:
        token = secrets.token_urlsafe(4)
        code = ''.join([c for c in token if c.isalnum()])[:length]
        if len(code) < length:
            continue
        if not _code_exists(code):
            return code


def add_url(url: str, expires_at=None, password=None) -> str:
    """Store a URL and return its short code.

    ``expires_at`` is a Unix timestamp, or None for a link that never expires.
    """
    url = _normalize_url(url)
    password_hash = generate_password_hash(password) if password else None
    conn = get_conn()
    cur = conn.cursor()
    for _ in range(5):
        code = generate_code()
        try:
            cur.execute(
                "INSERT INTO urls (code, url, created_at, expires_at, password_hash) VALUES (?, ?, ?, ?, ?)",
                (code, url, time.time(), expires_at, password_hash),
            )
            conn.commit()
            conn.close()
            return code
        except sqlite3.IntegrityError:
            continue
    conn.close()
    raise RuntimeError("Failed to create unique code")


def is_expired(expires_at) -> bool:
    return expires_at is not None and expires_at <= time.time()


def get_record(code: str):
    """Return the full row for a code, or None if it does not exist."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM urls WHERE code = ?", (code,)).fetchone()
    conn.close()
    return row


def get_url(code: str):
    """Return the destination URL, or None if the code is missing or expired."""
    row = get_record(code)
    if row is None or is_expired(row["expires_at"]):
        return None
    return row["url"]


def has_password(row) -> bool:
    if row is None:
        return False
    return bool(row["password_hash"])


def verify_password(row, password) -> bool:
    if row is None:
        return False
    password_hash = row["password_hash"]
    if not password_hash:
        return True
    return check_password_hash(password_hash, password or "")


def increment_visits(code: str):
    conn = get_conn()
    conn.execute("UPDATE urls SET visits = visits + 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()


def parse_expiry(expires_in=None, expires_at=None, now=None):
    """Turn an expiry request into a Unix timestamp (or None for "never").

    ``expires_in`` is a number of seconds from now. ``expires_at`` is a Unix
    timestamp or an ISO 8601 date/time. Raises ValueError for invalid input.
    """
    now = time.time() if now is None else now

    if expires_in not in (None, ""):
        try:
            seconds = float(expires_in)
        except (TypeError, ValueError):
            raise ValueError("expires_in must be a number of seconds")
        if seconds <= 0:
            raise ValueError("expires_in must be greater than zero")
        if seconds > MAX_EXPIRY_SECONDS:
            raise ValueError("expires_in is too far in the future")
        return now + seconds

    if expires_at in (None, ""):
        return None

    if isinstance(expires_at, (int, float)):
        timestamp = float(expires_at)
    else:
        text = str(expires_at).strip()
        try:
            timestamp = float(text)
        except ValueError:
            try:
                moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(
                    "expires_at must be an ISO 8601 date/time or a Unix timestamp"
                )
            if moment.tzinfo is None:
                moment = moment.astimezone()
            timestamp = moment.timestamp()

    if timestamp <= now:
        raise ValueError("expiration must be in the future")
    if timestamp > now + MAX_EXPIRY_SECONDS:
        raise ValueError("expiration is too far in the future")
    return timestamp


def format_expiry(expires_at):
    """Format a Unix timestamp as an ISO 8601 UTC string, or None."""
    if expires_at is None:
        return None
    return datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()
