import os
import psycopg2
from fastapi import APIRouter, HTTPException, status
from backend.models import EnrollRequest
from backend.services import auth, zepiris_client

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

@router.post("/enroll")
async def enroll(request: EnrollRequest):
    # Validate the API key
    org = auth.validate_api_key(request.org_api_key)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )

    # Call ZepIris service to enroll the worker's face
    try:
        await zepiris_client.enroll_face(request.worker_id, request.image_base64)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Biometric enrollment service error: {str(e)}"
        )

    # Insert worker details in database
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database URL is not configured."
        )

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO workers (worker_id, org_id) VALUES (%s, %s);",
                    (request.worker_id, org.id)
                )
    except psycopg2.IntegrityError:
        # If the worker is already enrolled for this org
        pass
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record worker registration in database: {str(e)}"
        )

    return {"success": True, "worker_id": request.worker_id}
