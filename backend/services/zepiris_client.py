# backend/services/zepiris_client.py: Client service for interacting with the ZepIris facial authentication server.

import os
import base64
import json
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

ZEPIRIS_URL = os.getenv("ZEPIRIS_URL")
ZEPIRIS_THRESHOLD = float(os.getenv("ZEPIRIS_THRESHOLD", "0.4"))

_client = None

def get_httpx_client() -> httpx.AsyncClient:
    """Gets or initializes the global AsyncClient for connection pooling."""
    global _client
    if _client is None:
        # Keepalive limits: 10 connections keepalive, max 50 concurrent connections
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
        _client = httpx.AsyncClient(limits=limits, timeout=10.0)
    return _client

async def close_httpx_client():
    """Closes the global AsyncClient."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None

async def _post_with_retries(client: httpx.AsyncClient, url: str, data: dict, files: dict, max_retries: int = 3) -> httpx.Response:
    """Helper to send POST request with retries and exponential backoff for transient failures."""
    attempt = 0
    backoff = 0.5  # initial sleep duration in seconds
    while True:
        try:
            response = await client.post(url, data=data, files=files)
            if response.status_code in (502, 503, 504):
                response.raise_for_status()
            return response
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            attempt += 1
            if attempt >= max_retries:
                raise e
            await asyncio.sleep(backoff)
            backoff *= 2

async def enroll_face(worker_id: str, image_base64: str, tenant: str) -> dict:
    """Enrolls a worker's face image in the ZepIris system asynchronously."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
    
    # Decode base64 image to raw bytes, with error handling
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        raise ValueError(f"Invalid Base64 image payload: {str(e)}")

    client = get_httpx_client()
    try:
        response = await _post_with_retries(
            client,
            f"{ZEPIRIS_URL}/v1/faces/insert",
            data={"id": worker_id, "tenant": tenant},
            files={"file": ("face.jpg", image_bytes, "image/jpeg")}
        )
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Biometric enrollment failed to communicate with ZepIris server. Error: {str(e)}") from e

async def verify_face(worker_id: str, image_base64: str, tenant: str) -> dict:
    """Verifies a worker's face image against ZepIris search matches asynchronously."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
        
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        raise ValueError(f"Invalid Base64 image payload: {str(e)}")

    client = get_httpx_client()
    try:
        response = await _post_with_retries(
            client,
            f"{ZEPIRIS_URL}/v1/faces/search",
            data={"tenant": tenant},
            files={"file": ("face.jpg", image_bytes, "image/jpeg")}
        )
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
    except Exception as e:
        raise RuntimeError(f"Biometric verification failed to communicate with ZepIris server. Error: {str(e)}") from e
