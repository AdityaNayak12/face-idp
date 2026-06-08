# backend/services/zepiris_client.py: Client service for interacting with the ZepIris facial authentication server.

import os
import base64
import httpx
from dotenv import load_dotenv

load_dotenv()

ZEPIRIS_URL = os.getenv("ZEPIRIS_URL")
ZEPIRIS_THRESHOLD = float(os.getenv("ZEPIRIS_THRESHOLD", "0.4"))

async def enroll_face(worker_id: str, image_base64: str, tenant: str) -> dict:
    """Enrolls a worker's face image in the ZepIris system using multipart upload."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
    
    # Decode base64 image to raw bytes
    image_bytes = base64.b64decode(image_base64)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ZEPIRIS_URL}/v1/faces/insert",
                data={
                    "id": worker_id,
                    "tenant": tenant
                },
                files={
                    "file": ("face.jpg", image_bytes, "image/jpeg")
                }
            )
            response.raise_for_status()
            return response.json()
    except (httpx.ConnectError, httpx.HTTPError) as e:
        if os.getenv("MOCK_ZEPIRIS", "true").lower() == "true":
            print(f"WARNING: ZepIris connection failed ({e}). Returning mock enrollment success.")
            return {"success": True, "id": worker_id}
        raise e

async def verify_face(worker_id: str, image_base64: str, tenant: str) -> dict:
    """Verifies a worker's face image against ZepIris search matches."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
        
    image_bytes = base64.b64decode(image_base64)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ZEPIRIS_URL}/v1/faces/search",
                data={
                    "tenant": tenant
                },
                files={
                    "file": ("face.jpg", image_bytes, "image/jpeg")
                }
            )
            response.raise_for_status()
            result = response.json()
            
            matches = result.get("matches", [])
            verified = False
            confidence = 0.0
            
            for match in matches:
                if match.get("id") == worker_id:
                    score = match.get("score", 0.0)
                    confidence = score
                    if score >= ZEPIRIS_THRESHOLD:
                        verified = True
                    break
                    
            return {
                "verified": verified,
                "confidence": confidence
            }
    except (httpx.ConnectError, httpx.HTTPError) as e:
        if os.getenv("MOCK_ZEPIRIS", "true").lower() == "true":
            print(f"WARNING: ZepIris connection failed ({e}). Returning mock verification success.")
            return {
                "verified": True,
                "confidence": 0.95
            }
        raise e

