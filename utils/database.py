"""
Database Helper — Uses raw SQL queries (intentionally vulnerable to SQL injection).
Each sandbox gets its own SQLite database file.
"""
import sqlite3
import os


def get_db_path(sandbox_id):
    """Get the SQLite database path for a sandbox."""
    from config import Config
    return os.path.join(Config.SANDBOX_DIR, sandbox_id, 'db.sqlite')


def get_connection(sandbox_id):
    """Get a database connection for a sandbox."""
    db_path = get_db_path(sandbox_id)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def query_one(sandbox_id, sql, params=None):
    """Execute query and return one row."""
    conn = get_connection(sandbox_id)
    try:
        if params:
            row = conn.execute(sql, params).fetchone()
        else:
            row = conn.execute(sql).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def query_all(sandbox_id, sql, params=None):
    """Execute query and return all rows."""
    conn = get_connection(sandbox_id)
    try:
        if params:
            rows = conn.execute(sql, params).fetchall()
        else:
            rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def execute(sandbox_id, sql, params=None):
    """Execute a write query (INSERT/UPDATE/DELETE)."""
    conn = get_connection(sandbox_id)
    try:
        if params:
            conn.execute(sql, params)
        else:
            conn.execute(sql)
        conn.commit()
    finally:
        conn.close()


def execute_returning_id(sandbox_id, sql, params=None):
    """Execute INSERT and return the new row ID."""
    conn = get_connection(sandbox_id)
    try:
        cursor = conn.execute(sql, params or [])
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def execute_raw(sandbox_id, sql):
    """
    Execute raw SQL without parameterization.
    VULNERABILITY: Used by search endpoint — enables SQL injection.
    """
    conn = get_connection(sandbox_id)
    try:
        rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise e
    finally:
        conn.close()
