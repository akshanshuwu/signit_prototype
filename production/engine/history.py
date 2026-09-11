"""Local history store — F2 (functional core, no widgets yet).

SQLite, local-only, offline. One row per successful live/synth chain run.
History failure must never break the analysis chain (callers wrap in
try/except and log "history warn: ...").

Dev default: ~/.signit/history.db
Windows:     %APPDATA%/SIGNIT/history.db
Tests/CI:    pass an explicit tmp path (or --history-db).
"""
from __future__ import annotations

import datetime
import os
import sqlite3
import sys

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    fs INTEGER NOT NULL,
    fc REAL NOT NULL,
    kind TEXT NOT NULL,
    modulation TEXT NOT NULL,
    confidence REAL NOT NULL,
    snr REAL NOT NULL,
    bw REAL NOT NULL,
    symbol_rate INTEGER NOT NULL,
    source TEXT NOT NULL
);
"""


def default_db_path() -> str:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "SIGNIT", "history.db")
    return os.path.join(os.path.expanduser("~"), ".signit", "history.db")


def _connect(path: str) -> sqlite3.Connection:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute(SCHEMA)
    con.commit()
    return con


def init_db(path: str) -> str:
    """Create parent dirs + table if missing. Returns path."""
    con = _connect(path)
    con.close()
    return path


def record_run(path: str, row: dict) -> int:
    """Insert one run row. Returns rowid. Raises on bad input/IO."""
    con = _connect(path)
    try:
        cur = con.execute(
            "INSERT INTO runs (ts, filename, sha256, fs, fc, kind, modulation,"
            " confidence, snr, bw, symbol_rate, source)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                row.get("ts") or datetime.datetime.now().isoformat(timespec="seconds"),
                str(row.get("filename", "—")),
                str(row.get("sha256", "")),
                int(row.get("fs", 0)),
                float(row.get("fc", 0.0)),
                str(row.get("kind", "iq")),
                str(row.get("modulation", "UNKNOWN")),
                float(row.get("confidence", 0.0)),
                float(row.get("snr", 0.0)),
                float(row.get("bw", 0.0)),
                int(row.get("symbol_rate", 0)),
                str(row.get("source", "live")),
            ),
        )
        con.commit()
        return int(cur.lastrowid)
    finally:
        con.close()


def list_runs(path: str, limit: int = 100) -> list[dict]:
    """Newest-first run summaries. Returns [] when DB is missing/empty."""
    if not os.path.isfile(path):
        return []
    con = sqlite3.connect(path)
    try:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            "SELECT id, ts, filename, sha256, fs, fc, kind, modulation,"
            " confidence, snr, bw, symbol_rate, source"
            " FROM runs ORDER BY id DESC LIMIT ?",
            (int(limit),),
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def get_run(path: str, rowid: int) -> dict | None:
    """Fetch one run by id, or None."""
    if not os.path.isfile(path):
        return None
    con = sqlite3.connect(path)
    try:
        con.row_factory = sqlite3.Row
        cur = con.execute(
            "SELECT id, ts, filename, sha256, fs, fc, kind, modulation,"
            " confidence, snr, bw, symbol_rate, source"
            " FROM runs WHERE id = ?",
            (int(rowid),),
        )
        r = cur.fetchone()
        return dict(r) if r is not None else None
    finally:
        con.close()
