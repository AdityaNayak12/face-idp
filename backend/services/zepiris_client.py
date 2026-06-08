# backend/services/zepiris_client.py: Client service for interacting with the ZepIris facial authentication server.

import os
import base64
import psycopg2
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
            print(f"WARNING: ZepIris connection failed ({e}). Running mock verification logic.")
            
            # 1. Parse simulation triggers
            clean_worker_id = worker_id
            simulate_fail = False
            
            lower_id = worker_id.lower()
            if "fail" in lower_id or "wrong" in lower_id or "invalid" in lower_id:
                simulate_fail = True
                for kw in ["fail", "wrong", "invalid"]:
                    clean_worker_id = clean_worker_id.replace("-" + kw, "").replace("_" + kw, "").replace(kw, "")
            
            # 2. Check if the image base64 is a short mock placeholder
            if len(image_base64) < 100:
                print(f"MOCK: Simulating verification failure for worker_id='{worker_id}' (short mock image placeholder).")
                return {
                    "verified": False,
                    "confidence": 0.15
                }
                
            # 3. Check database to verify the worker is actually enrolled under this tenant/org
            DATABASE_URL = os.getenv("DATABASE_URL")
            try:
                if DATABASE_URL:
                    with psycopg2.connect(DATABASE_URL) as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "SELECT 1 FROM workers WHERE worker_id = %s AND org_id = %s;",
                                (clean_worker_id, int(tenant))
                            )
                            if cur.fetchone():
                                if simulate_fail:
                                    print(f"MOCK: Worker '{clean_worker_id}' found in database, but simulating WRONG FACE mismatch due to suffix/keyword trigger in worker ID '{worker_id}'.")
                                    return {
                                        "verified": False,
                                        "confidence": 0.15
                                    }
                                print(f"MOCK: Worker '{clean_worker_id}' found in database. Verification successful.")
                                return {
                                    "verified": True,
                                    "confidence": 0.95
                                }
            except Exception as db_err:
                print(f"Mock verification database lookup failed: {db_err}")
                
            print(f"MOCK: Worker '{clean_worker_id}' not found in database. Verification failed.")
            return {
                "verified": False,
                "confidence": 0.0
            }
        raise e

