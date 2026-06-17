import os
from ..db import get_async_db_connection
from fastapi import APIRouter, HTTPException, status, Query, Header
from ..services import auth

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

@router.get("/logs")
async def get_logs(
    x_api_key: str | None = Header(None, alias="X-API-Key", description="API key of the organization"),
    api_key: str | None = Query(None, description="API key of the organization (Deprecated, use X-API-Key header)")
):
    # Determine the API key to use (header prioritized)
    key = x_api_key or api_key
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing. Use 'X-API-Key' header."
        )

    # Validate the API key asynchronously
    org = await auth.validate_api_key(key)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )
 
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database URL is not configured."
        )

    try:
        async with get_async_db_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, org_id, worker_id, confidence, verified, timestamp 
                FROM verification_logs 
                WHERE org_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 100;
                """,
                org.id
            )
            
            logs = [
                {
                    "id": row['id'],
                    "org_id": row['org_id'],
                    "worker_id": row['worker_id'],
                    "confidence": row['confidence'],
                    "verified": row['verified'],
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None
                }
                for row in rows
            ]
            return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query database logs: {str(e)}"
        )
