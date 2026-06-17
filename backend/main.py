# backend/main.py: Entry point for the face-idp FastAPI backend application.

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import enroll, verify, logs
from .db import init_async_pool, close_async_pool
from .services.zepiris_client import close_httpx_client
from .services.auth import hash_api_key

DATABASE_URL = os.getenv("DATABASE_URL")
MASTER_API_KEY = os.getenv("MASTER_API_KEY")

def init_db():
    """Initializes the database using a transient psycopg2 connection (run once on startup)."""
    if not DATABASE_URL:
        print("DATABASE_URL is not set in the environment. Skipping database initialization.")
        return

    create_tables_queries = [
        """
        CREATE TABLE IF NOT EXISTS orgs (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            api_key VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS workers (
            id SERIAL PRIMARY KEY,
            worker_id VARCHAR(255) NOT NULL,
            org_id INTEGER REFERENCES orgs(id) ON DELETE CASCADE,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (worker_id, org_id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS verification_logs (
            id SERIAL PRIMARY KEY,
            org_id INTEGER REFERENCES orgs(id) ON DELETE CASCADE,
            worker_id VARCHAR(255) NOT NULL,
            confidence FLOAT NOT NULL,
            verified BOOLEAN NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        # Indexes for production query performance and join efficiency
        """
        CREATE INDEX IF NOT EXISTS idx_workers_org_id ON workers(org_id);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_verification_logs_org_timestamp ON verification_logs(org_id, timestamp DESC);
        """
    ]

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn:
            with conn.cursor() as cur:
                # Create tables and indexes
                for query in create_tables_queries:
                    cur.execute(query)
                
                # Insert default organization if no orgs exist
                cur.execute("SELECT COUNT(*) FROM orgs;")
                count = cur.fetchone()[0]
                if count == 0:
                    if MASTER_API_KEY:
                        cur.execute(
                            "INSERT INTO orgs (name, email, api_key) VALUES (%s, %s, %s);",
                            ("default", "default@example.com", hash_api_key(MASTER_API_KEY))
                        )
                        print("Inserted default organization with hashed MASTER_API_KEY.")
                    else:
                        print("WARNING: No organizations exist, and MASTER_API_KEY is not defined in .env.")
    except Exception as e:
        print(f"Error during database initialization: {e}")
    finally:
        if conn:
            conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions: initialize database, connection pool
    await init_async_pool()
    init_db()
    yield
    # Shutdown actions: clean up pools
    await close_async_pool()
    await close_httpx_client()

app = FastAPI(
    title="face-idp API",
    description="Identity-as-a-Service layer built on top of ZepIris facial authentication.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-API-Key"],
)

# Register routes
app.include_router(enroll.router, tags=["Enrollment"])
app.include_router(verify.router, tags=["Verification"])
app.include_router(logs.router, tags=["Audit Logs"])

@app.get("/health")
async def health():
    return {"status": "ok"}
