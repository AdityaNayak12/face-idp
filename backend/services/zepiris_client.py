# backend/services/zepiris_client.py: Client service for interacting with the ZepIris facial authentication server.

import os
import base64
import json
import uuid
import asyncio
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

ZEPIRIS_URL = os.getenv("ZEPIRIS_URL")
ZEPIRIS_THRESHOLD = float(os.getenv("ZEPIRIS_THRESHOLD", "0.4"))

def _sync_multipart_post(url: str, fields: dict, files: dict) -> str:
    """Helper to send a multipart/form-data POST request synchronously using urllib."""
    boundary = uuid.uuid4().hex
    parts = []
    
    # Form fields
    for name, value in fields.items():
        parts.append(f"--{boundary}".encode('utf-8'))
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode('utf-8'))
        parts.append(b'')
        parts.append(str(value).encode('utf-8'))
        
    # Files
    for name, (filename, file_bytes, content_type) in files.items():
        parts.append(f"--{boundary}".encode('utf-8'))
        parts.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode('utf-8'))
        parts.append(f'Content-Type: {content_type}'.encode('utf-8'))
        parts.append(b'')
        parts.append(file_bytes)
        
    parts.append(f"--{boundary}--".encode('utf-8'))
    parts.append(b'')
    
    body = b'\r\n'.join(parts)
    
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Content-Length', str(len(body)))
    
    # Use urllib to send request with a reasonable timeout
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode('utf-8')

async def enroll_face(worker_id: str, image_base64: str, tenant: str) -> dict:
    """Enrolls a worker's face image in the ZepIris system using multipart upload."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
    
    # Decode base64 image to raw bytes
    image_bytes = base64.b64decode(image_base64)
    
    try:
        response_str = await asyncio.to_thread(
            _sync_multipart_post,
            f"{ZEPIRIS_URL}/v1/faces/insert",
            {"id": worker_id, "tenant": tenant},
            {"file": ("face.jpg", image_bytes, "image/jpeg")}
        )
        return json.loads(response_str)
    except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
        raise RuntimeError(f"Biometric enrollment failed to communicate with ZepIris server at {ZEPIRIS_URL}. Error: {str(e)}") from e

async def verify_face(worker_id: str, image_base64: str, tenant: str) -> dict:
    """Verifies a worker's face image against ZepIris search matches."""
    if not ZEPIRIS_URL:
        raise ValueError("ZEPIRIS_URL is not set in the environment variables.")
        
    image_bytes = base64.b64decode(image_base64)
    
    try:
        response_str = await asyncio.to_thread(
            _sync_multipart_post,
            f"{ZEPIRIS_URL}/v1/faces/search",
            {"tenant": tenant},
            {"file": ("face.jpg", image_bytes, "image/jpeg")}
        )
        result = json.loads(response_str)
        
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
    except (urllib.error.HTTPError, urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
        raise RuntimeError(f"Biometric verification failed to communicate with ZepIris server at {ZEPIRIS_URL}. Error: {str(e)}") from e
