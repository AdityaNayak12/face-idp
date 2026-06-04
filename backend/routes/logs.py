# backend/routes/logs.py: API routes for retrieving audit and verification logs.

import os
import psycopg2
from fastapi import APIRouter, HTTPException, status, Query
from backend.services import auth

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

@router.get("/logs")
async def get_logs(api_key: str = Query(..., description="API key of the organization")):
    # Validate the API key
    org = auth.validate_api_key(api_key)
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
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, org_id, worker_id, confidence, verified, timestamp 
                    FROM verification_logs 
                    WHERE org_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT 100;
                    """,
                    (org.id,)
                )
                rows = cur.fetchall()
                
                logs = [
                    {
                        "id": row[0],
                        "org_id": row[1],
                        "worker_id": row[2],
                        "confidence": row[3],
                        "verified": row[4],
                        "timestamp": row[5].isoformat() if row[5] else None
                    }
                    for row in rows
                ]
                return logs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query database logs: {str(e)}"
        )
