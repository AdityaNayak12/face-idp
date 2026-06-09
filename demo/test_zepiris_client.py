# demo/test_zepiris_client.py: Unit tests for ZepIris client service.

import sys
import os
import unittest
from unittest.mock import AsyncMock, patch
import urllib.error

# Ensure project root directory is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import zepiris_client

class TestZepirisClient(unittest.IsolatedAsyncioTestCase):
    @patch("backend.services.zepiris_client._sync_multipart_post")
    async def test_enroll_face(self, mock_post):
        # Setup mock response
        mock_post.return_value = '{"success": true, "id": "test-worker-001"}'

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            result = await zepiris_client.enroll_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertEqual(result, {"success": True, "id": "test-worker-001"})
        mock_post.assert_called_once_with(
            "http://mock-zepiris:8080/v1/faces/insert",
            {"id": "test-worker-001", "tenant": "123"},
            {"file": ("face.jpg", b'\x89PNG\r\n\x1a\n', "image/jpeg")}
        )

    @patch("backend.services.zepiris_client._sync_multipart_post")
    async def test_verify_face_match(self, mock_post):
        # Setup mock response for search returning a match
        mock_post.return_value = '{"matches": [{"id": "test-worker-001", "score": 0.95}, {"id": "test-worker-002", "score": 0.50}]}'

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "ZEPIRIS_THRESHOLD": "0.6"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            zepiris_client.ZEPIRIS_THRESHOLD = 0.6
            result = await zepiris_client.verify_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertTrue(result["verified"])
        self.assertEqual(result["confidence"], 0.95)
        mock_post.assert_called_once_with(
            "http://mock-zepiris:8080/v1/faces/search",
            {"tenant": "123"},
            {"file": ("face.jpg", b'\x89PNG\r\n\x1a\n', "image/jpeg")}
        )

    @patch("backend.services.zepiris_client._sync_multipart_post")
    async def test_verify_face_below_threshold(self, mock_post):
        # Setup mock response for search returning match below threshold
        mock_post.return_value = '{"matches": [{"id": "test-worker-001", "score": 0.45}]}'

        # Execute
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "ZEPIRIS_THRESHOLD": "0.6"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            zepiris_client.ZEPIRIS_THRESHOLD = 0.6
            result = await zepiris_client.verify_face("test-worker-001", "iVBORw0KGgo=", "123")
            
        # Verify
        self.assertFalse(result["verified"])
        self.assertEqual(result["confidence"], 0.45)

    @patch("backend.services.zepiris_client._sync_multipart_post", side_effect=urllib.error.URLError("Connection refused"))
    @patch("psycopg2.connect")
    async def test_verify_face_mock_fallback_success(self, mock_db_connect, mock_post):
        # Mock database connection and query to return success
        mock_conn = mock_db_connect.return_value
        mock_cur = mock_conn.cursor.return_value
        mock_cur.fetchone.return_value = (1,)

        # Execute with a sufficiently long image base64 (e.g. 100+ chars) to not trigger the short image check
        long_image = "a" * 120
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "MOCK_ZEPIRIS": "true"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            result = await zepiris_client.verify_face("test-worker-001", long_image, "123")

        self.assertTrue(result["verified"])
        self.assertEqual(result["confidence"], 0.95)

    @patch("backend.services.zepiris_client._sync_multipart_post", side_effect=urllib.error.URLError("Connection refused"))
    @patch("psycopg2.connect")
    async def test_verify_face_mock_fallback_fail_keyword(self, mock_db_connect, mock_post):
        # Mock connection and cursor context managers
        mock_conn = mock_db_connect.return_value.__enter__.return_value
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchone.return_value = (1,)

        # Execute with "fail" in worker_id
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "MOCK_ZEPIRIS": "true"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            result = await zepiris_client.verify_face("test-worker-fail", "a" * 120, "123")

        self.assertFalse(result["verified"])
        self.assertEqual(result["confidence"], 0.15)

    @patch("backend.services.zepiris_client._sync_multipart_post", side_effect=urllib.error.URLError("Connection refused"))
    @patch("psycopg2.connect")
    async def test_verify_face_mock_fallback_success_cleaned_fail(self, mock_db_connect, mock_post):
        # Mock connection and cursor context managers
        mock_conn = mock_db_connect.return_value.__enter__.return_value
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchone.return_value = (1,)

        long_image = "a" * 120
        with patch.dict(os.environ, {"ZEPIRIS_URL": "http://mock-zepiris:8080", "MOCK_ZEPIRIS": "true"}):
            zepiris_client.ZEPIRIS_URL = "http://mock-zepiris:8080"
            result = await zepiris_client.verify_face("test-worker-001-fail", long_image, "123")

        # The query should be for "test-worker-001", but the result should be False
        self.assertFalse(result["verified"])
        self.assertEqual(result["confidence"], 0.15)
        # Ensure database query checked the clean ID "test-worker-001"
        mock_cur.execute.assert_called_with(
            "SELECT 1 FROM workers WHERE worker_id = %s AND org_id = %s;",
            ("test-worker-001", 123)
        )

if __name__ == "__main__":
    unittest.main()
