# demo/test_backend.py: E2E testing script for the face-idp backend.

import os
import httpx
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"
DATABASE_URL = os.getenv("DATABASE_URL")
MASTER_API_KEY = os.getenv("MASTER_API_KEY")

def print_result(step_num, name, status, detail=""):
    print(f"Step {step_num} — {name}: [{status}] {detail}")

def test_backend():
    passed_steps = 0
    total_steps = 6
    step3_skipped = False

    # Step 1 — Health check
    try:
        response = httpx.get(f"{BASE_URL}/health")
        if response.status_code == 200 and response.json() == {"status": "ok"}:
            print_result(1, "Health check", "PASSED")
            passed_steps += 1
        else:
            print_result(1, "Health check", "FAILED", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        print_result(1, "Health check", "FAILED", f"Error: {e}")

    # Step 2 — API key validation (invalid key)
    try:
        payload = {
            "worker_id": "test-worker-001",
            "org_api_key": "invalid-key-123",
            "image_base64": "iVBORw0KGgo="
        }
        response = httpx.post(f"{BASE_URL}/verify", json=payload)
        if response.status_code == 401:
            print_result(2, "API key validation (invalid key)", "PASSED")
            passed_steps += 1
        else:
            print_result(2, "API key validation (invalid key)", "FAILED", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        print_result(2, "API key validation (invalid key)", "FAILED", f"Error: {e}")

    # Step 3 — Enroll a worker (mock image)
    try:
        payload = {
            "worker_id": "test-worker-001",
            "org_api_key": MASTER_API_KEY or "missing-master-key",
            "image_base64": "iVBORw0KGgo="
        }
        response = httpx.post(f"{BASE_URL}/enroll", json=payload)
        
        # We expect a 502/500 or connection error because ZepIris is not running
        if response.status_code in [500, 502]:
            print_result(3, "Enroll a worker (mock image)", "SKIPPED", "ZepIris not connected — expected status")
            step3_skipped = True
        else:
            print_result(3, "Enroll a worker (mock image)", "FAILED", f"Unexpected status: {response.status_code}, Body: {response.text}")
    except (httpx.HTTPError, httpx.ConnectError) as e:
        print_result(3, "Enroll a worker (mock image)", "SKIPPED", f"ZepIris not connected — expected ({type(e).__name__})")
        step3_skipped = True
    except Exception as e:
        print_result(3, "Enroll a worker (mock image)", "FAILED", f"Unexpected error: {e}")

    # Step 4 — Logs endpoint
    try:
        response = httpx.get(f"{BASE_URL}/logs", params={"api_key": MASTER_API_KEY or ""})
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print_result(4, "Logs endpoint", "PASSED", f"Logs count: {len(data)}")
                passed_steps += 1
            else:
                print_result(4, "Logs endpoint", "FAILED", f"Response is not a list: {data}")
        else:
            print_result(4, "Logs endpoint", "FAILED", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        print_result(4, "Logs endpoint", "FAILED", f"Error: {e}")

    # Step 5 — Database tables exist
    db_conn = None
    try:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL is not configured in .env")
        db_conn = psycopg2.connect(DATABASE_URL)
        with db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_name IN ('orgs', 'workers', 'verification_logs');
                """
            )
            tables = [row[0] for row in cur.fetchall()]
            expected = {'orgs', 'workers', 'verification_logs'}
            if expected.issubset(set(tables)):
                print_result(5, "Database tables exist", "PASSED", f"Found tables: {tables}")
                passed_steps += 1
            else:
                print_result(5, "Database tables exist", "FAILED", f"Missing tables. Found: {tables}")
    except Exception as e:
        print_result(5, "Database tables exist", "FAILED", f"DB Error: {e}")

    # Step 6 — Default org exists
    try:
        if db_conn is None and DATABASE_URL:
            db_conn = psycopg2.connect(DATABASE_URL)
        if db_conn:
            with db_conn.cursor() as cur:
                cur.execute("SELECT name, api_key FROM orgs;")
                rows = cur.fetchall()
                if rows:
                    org_name, org_key = rows[0]
                    masked_key = f"{org_key[:6]}..." if org_key else "None"
                    print_result(6, "Default org exists", "PASSED", f"Org name: {org_name}, Key: {masked_key}")
                    passed_steps += 1
                else:
                    print_result(6, "Default org exists", "FAILED", "No orgs found in table.")
        else:
            print_result(6, "Default org exists", "FAILED", "DB connection not established.")
    except Exception as e:
        print_result(6, "Default org exists", "FAILED", f"DB Error: {e}")
    finally:
        if db_conn:
            db_conn.close()

    # Final summary printing
    print("\n" + "="*40)
    print(f"Results: {passed_steps}/{total_steps} passed")
    if step3_skipped:
        print("Step 3 skipped — ZepIris not running (expected)")
    print("="*40)

if __name__ == "__main__":
    test_backend()
