"""State + deduplication.

The repo itself is our memory: this SQLite file is committed back at the end of
every run, so the next run knows which stories are already used and never
repeats one. Each story is recorded the moment it is PRODUCED (regardless of
whether you later approve or discard the upload), so a discarded story is not
re-sourced and re-narrated tomorrow.
"""
import os
import re
import sqlite3
import hashlib
import difflib
from . import config


def _norm(title: str) -> str:
    """Normalise a headline for fuzzy comparison."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def connect():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT UNIQUE,          -- hash of normalised title
            norm_title  TEXT,
            source_url  TEXT,
            status      TEXT,                 -- produced | published | discarded
            video_id    TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def fingerprint(title: str) -> str:
    return hashlib.sha256(_norm(title).encode()).hexdigest()[:16]


def is_duplicate(conn, title: str) -> bool:
    """True if we've seen this story before (exact fingerprint OR a near-match
    on the normalised title, to catch the same event reported by another
    outlet with slightly different wording)."""
    fp = fingerprint(title)
    cur = conn.execute("SELECT 1 FROM stories WHERE fingerprint=?", (fp,))
    if cur.fetchone():
        return True
    nt = _norm(title)
    for (existing,) in conn.execute("SELECT norm_title FROM stories"):
        if difflib.SequenceMatcher(None, nt, existing).ratio() > 0.80:
            return True
    return False


def record_produced(conn, title: str, source_url: str, video_id: str) -> int:
    fp = fingerprint(title)
    cur = conn.execute(
        "INSERT OR IGNORE INTO stories (fingerprint, norm_title, source_url, status, video_id) "
        "VALUES (?,?,?,?,?)",
        (fp, _norm(title), source_url, "produced", video_id),
    )
    conn.commit()
    return cur.lastrowid
