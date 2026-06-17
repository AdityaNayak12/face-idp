import os
import secrets
import hashlib
from backend.db import get_async_db_connection
from dotenv import load_dotenv
from ..models import Org

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def generate_api_key() -> str:
    """Generates a random 32-character hex string (16 bytes)."""
    return secrets.token_hex(16)

def hash_api_key(api_key: str) -> str:
    """Computes a SHA-256 hash of the API key to safely store or query in the database."""
    return hashlib.sha256(api_key.strip().encode('utf-8')).hexdigest()

async def validate_api_key(api_key: str) -> Org | None:
    """Queries Postgres asynchronously to check if the hashed api_key belongs to an active org."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in the environment variables.")
    
    if not api_key:
        return None

    hashed_key = hash_api_key(api_key)
    
    try:
        async with get_async_db_connection() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, email, api_key, created_at FROM orgs WHERE api_key = $1;",
                hashed_key
            )
            if row:
                return Org(
                    id=row['id'],
                    name=row['name'],
                    email=row['email'],
                    api_key=row['api_key'],
                    created_at=row['created_at']
                )
    except Exception as e:
        print(f"Database error during API key validation: {e}")
        raise e
        
    return None
