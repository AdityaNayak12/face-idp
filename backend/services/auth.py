import os
import secrets
from backend.db import get_db_connection
from dotenv import load_dotenv
from ..models import Org

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def generate_api_key() -> str:
    """Generates a random 32-character hex string (16 bytes)."""
    return secrets.token_hex(16)

def validate_api_key(api_key: str) -> Org | None:
    """Queries Postgres to check if the api_key belongs to an active org."""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in the environment variables.")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, email, api_key, created_at FROM orgs WHERE api_key = %s;",
                    (api_key,)
                )
                row = cur.fetchone()
                if row:
                    return Org(
                        id=row[0],
                        name=row[1],
                        email=row[2],
                        api_key=row[3],
                        created_at=row[4]
                    )
    except Exception as e:
        print(f"Database error during API key validation: {e}")
        raise e
        
    return None
