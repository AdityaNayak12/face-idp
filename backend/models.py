from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel

class OrgCreate(BaseModel):
    name: str
    email: str

class EnrollRequest(BaseModel):
    worker_id: str
    org_api_key: str
    image_base64: str

class VerifyRequest(BaseModel):
    worker_id: str
    org_api_key: str
    image_base64: str

@dataclass
class Org:
    id: int
    name: str
    email: str
    api_key: str
    created_at: datetime

@dataclass
class VerificationLog:
    id: int
    org_id: int
    worker_id: str
    confidence: float
    verified: bool
    timestamp: datetime
