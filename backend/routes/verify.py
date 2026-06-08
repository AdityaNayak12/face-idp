# backend/routes/verify.py: API routes for worker face verification.

import os
import psycopg2
from fastapi import APIRouter, HTTPException, status
from ..models import VerifyRequest
from ..services import auth, zepiris_client

router = APIRouter()
DATABASE_URL = os.getenv("DATABASE_URL")

@router.post("/verify")
async def verify(request: VerifyRequest):
    # Validate the API key
    org = auth.validate_api_key(request.org_api_key)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key."
        )

    # Call ZepIris service to verify the worker's face
    try:
        zepiris_response = await zepiris_client.verify_face(request.worker_id, request.image_base64, tenant=str(org.id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Biometric verification service error: {str(e)}"
        )

    verified = zepiris_response.get("verified", False)
    confidence = zepiris_response.get("confidence", 0.0)

    # Record the verification attempt in the database
    if not DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database URL is not configured."
        )

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO verification_logs (org_id, worker_id, confidence, verified) VALUES (%s, %s, %s, %s);",
                    (org.id, request.worker_id, confidence, verified)
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
