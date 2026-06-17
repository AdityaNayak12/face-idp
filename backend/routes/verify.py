import os
from ..db import get_async_db_connection
from fastapi import APIRouter, HTTPException, status
from ..models import VerifyRequest
from ..services import auth, zepiris_client

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

@router.post("/verify")
async def verify(request: VerifyRequest):
    # Validate the API key asynchronously
    org = await auth.validate_api_key(request.org_api_key)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )

    # Call ZepIris service to verify the worker's face
    try:
        zepiris_response = await zepiris_client.verify_face(request.worker_id, request.image_base64, tenant=str(org.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Biometric verification service error: {str(e)}"
        )

    verified = zepiris_response.get("verified", False)
    confidence = zepiris_response.get("confidence", 0.0)

    # Record the verification attempt in the database asynchronously
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database URL is not configured."
        )

    try:
        async with get_async_db_connection() as conn:
            await conn.execute(
                """
                INSERT INTO verification_logs (org_id, worker_id, confidence, verified) 
                VALUES ($1, $2, $3, $4);
                """,
                org.id, request.worker_id, confidence, verified
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record verification attempt: {str(e)}"
        )

    return {
        "verified": verified,
        "confidence": confidence,
        "worker_id": request.worker_id
    }
