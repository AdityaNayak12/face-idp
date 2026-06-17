import os
import asyncpg
from ..db import get_async_db_connection
from fastapi import APIRouter, HTTPException, status
from ..models import EnrollRequest
from ..services import auth, zepiris_client

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

@router.post("/enroll")
async def enroll(request: EnrollRequest):
    # Validate the API key asynchronously
    org = await auth.validate_api_key(request.org_api_key)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )

    # Call ZepIris service to enroll the worker's face
    try:
        await zepiris_client.enroll_face(request.worker_id, request.image_base64, tenant=str(org.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Biometric enrollment service error: {str(e)}"
        )

    # Insert worker details in database asynchronously
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database URL is not configured."
        )

    try:
        async with get_async_db_connection() as conn:
            await conn.execute(
                "INSERT INTO workers (worker_id, org_id) VALUES ($1, $2);",
                request.worker_id, org.id
            )
    except asyncpg.exceptions.UniqueViolationError:
        # If the worker is already enrolled for this org, ignore it
        pass
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record worker registration in database: {str(e)}"
        )

    return {"success": True, "worker_id": request.worker_id}
