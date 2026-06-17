# backend/db.py: Asynchronous database connection pooling using asyncpg.

import os
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
_async_pool = None

async def init_async_pool(min_size=5, max_size=20):
    """Initializes the global asyncpg connection pool."""
    global _async_pool
    if not DATABASE_URL:
        print("DATABASE_URL is not set. Async database pool will not be initialized.")
        return
    if _async_pool is None:
        try:
            _async_pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=min_size,
                max_size=max_size
            )
            print("Async database connection pool initialized.")
        except Exception as e:
            print(f"Failed to initialize async database connection pool: {e}")
            raise e

async def close_async_pool():
    """Closes the global asyncpg connection pool."""
    global _async_pool
    if _async_pool is not None:
        try:
            await _async_pool.close()
            print("Async database connection pool closed.")
        except Exception as e:
            print(f"Error closing async database connection pool: {e}")
        _async_pool = None

@asynccontextmanager
async def get_async_db_connection():
    """Context manager to lease an async connection from the pool and run it within a transaction."""
    global _async_pool
    if _async_pool is None:
        raise RuntimeError("Async database connection pool is not initialized. Call init_async_pool() first.")
    
    async with _async_pool.acquire() as conn:
        # Run queries in a transaction block
        async with conn.transaction():
            yield conn
