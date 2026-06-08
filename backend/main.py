# backend/main.py: Entry point for the face-idp FastAPI backend application.

import os
import psycopg2
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from .routes import enroll, verify, logs

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
MASTER_API_KEY = os.getenv("MASTER_API_KEY")

def init_db():
    """Initializes the database by creating tables if they do not exist and adding a default org."""
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
        """
    ]

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Create the tables
                for query in create_tables_queries:
                    cur.execute(query)
                
                # Insert default organization if no orgs exist
                cur.execute("SELECT COUNT(*) FROM orgs;")
                count = cur.fetchone()[0]
                if count == 0:
                    if MASTER_API_KEY:
                        cur.execute(
                            "INSERT INTO orgs (name, email, api_key) VALUES (%s, %s, %s);",
                            ("default", "default@example.com", MASTER_API_KEY)
                        )
                        print("Inserted default organization with MASTER_API_KEY.")
                    else:
                        print("WARNING: No organizations exist, and MASTER_API_KEY is not defined in .env.")
    except Exception as e:
        print(f"Error during database initialization: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    init_db()
    yield
    # Shutdown actions (if any)

app = FastAPI(
    title="face-idp API",
    description="Identity-as-a-Service layer built on top of ZepIris facial authentication.",
    version="1.0.0",
    lifespan=lifespan
)

# Register routes
app.include_router(enroll.router, tags=["Enrollment"])
app.include_router(verify.router, tags=["Verification"])
app.include_router(logs.router, tags=["Audit Logs"])

@app.get("/health")
async def health():
    return {"status": "ok"}
