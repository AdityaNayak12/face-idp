# backend/db.py: Database connection pooling and context management.

import os
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL")
_pool = None

def init_pool(minconn=1, maxconn=20):
    """Initializes the global connection pool."""
    global _pool
    if not DATABASE_URL:
        print("DATABASE_URL is not set. Database pool will not be initialized.")
        return
    if _pool is None:
        try:
            _pool = ThreadedConnectionPool(minconn, maxconn, DATABASE_URL)
            print("Database connection pool initialized.")
        except Exception as e:
            print(f"Failed to initialize database connection pool: {e}")
            raise e

def close_pool():
    """Closes the global connection pool."""
    global _pool
    if _pool is not None:
        try:
            _pool.closeall()
            print("Database connection pool closed.")
        except Exception as e:
            print(f"Error closing database connection pool: {e}")
        _pool = None

@contextmanager
def get_db_connection():
    """Context manager to lease a connection from the pool, wrap it in a transaction, and return it."""
    global _pool
    if _pool is None:
        raise RuntimeError("Database connection pool is not initialized. Call init_pool() first.")
    
    conn = _pool.getconn()
    try:
        with conn:  # Automatically commits on success, rolls back on exception
            yield conn
    finally:
        _pool.putconn(conn)
