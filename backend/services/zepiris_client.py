# backend/services/zepiris_client.py: Client service for interacting with the ZepIris facial authentication server.

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ZEPIRIS_URL = os.getenv("ZEPIRIS_URL")

async def enroll_face(worker_id: str, image_base64: str) -> dict:
    """Enrolls a worker's face image in the ZepIris system."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ZEPIRIS_URL}/v1/enroll",
            json={
                "user_id": worker_id,
                "image": image_base64
            }
        )
        response.raise_for_status()
        return response.json()

async def verify_face(worker_id: str, image_base64: str) -> dict:
    """Verifies a worker's face image against ZepIris."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ZEPIRIS_URL}/v1/verify",
            json={
                "user_id": worker_id,
                "image": image_base64
            }
        )
        response.raise_for_status()
        return response.json()
